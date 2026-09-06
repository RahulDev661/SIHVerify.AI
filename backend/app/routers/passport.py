"""
Passport verification endpoints.

Thin HTTP layer only — all real work happens in `ai_service`. Routes
here just: accept uploads, write them to a temp dir, call the
ai_service functions, translate exceptions into HTTP errors, and
clean up.
"""

import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from ai_service.document.detector import validate_document
from ai_service.face.cropper import crop_passport_face
from ai_service.face.detector import detect_faces
from ai_service.face.recognizer import compare_faces
from ai_service.ocr.extractor import process_passport
from ai_service.ocr.field_validator import compare_fields as compare_visible_to_mrz
from ai_service.ocr.visible_extractor import extract_visible_fields
from ai_service.tampering.detector import detect_tampering

from app.database import scan_history_collection
from app.routers.auth import get_current_user
from app.scoring import compute_score
from app.schemas import (
    DocumentValidationResult,
    FaceMatchResult,
    FieldConsistencyResult,
    MRZStructureValidation,
    PassportOCRResult,
    PassportVerificationResponse,
    ScanHistoryDetail,
    ScanHistorySummary,
    TamperingAnalysisResult,
    VisiblePassportFields,
)

router = APIRouter(prefix="/api/v1/passport", tags=["passport"])

ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/jpg"}

# Tampering statuses considered severe enough to fail verification
# outright, regardless of what MRZ/face/document checks say.
TAMPERING_BLOCKING_STATUSES = {"HIGH_RISK"}


def _save_upload(upload: UploadFile, dest_dir: Path) -> Path:
    if upload.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported content type: {upload.content_type}. "
            f"Allowed: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}",
        )

    suffix = Path(upload.filename or "").suffix or ".png"
    dest = dest_dir / (upload.filename or f"upload{suffix}")

    with dest.open("wb") as f:
        shutil.copyfileobj(upload.file, f)

    return dest


def _to_ocr_result(result: dict) -> PassportOCRResult:
    structure = result.get("structureValidation", {}) or {}
    return PassportOCRResult(
        passportNumber=result.get("passportNumber"),
        surname=result.get("surname"),
        givenNames=result.get("givenNames"),
        nationality=result.get("nationality"),
        dob=result.get("dob"),
        sex=result.get("sex"),
        expiry=result.get("expiry"),
        structureValidation=MRZStructureValidation(
            valid=structure.get("valid", False),
            errors=structure.get("errors", []),
        ),
    )


@router.post(
    "/ocr",
    response_model=PassportOCRResult,
    summary="Run OCR + MRZ extraction on a passport image (Module 1 only)",
)
async def ocr_passport(passport_image: UploadFile = File(...)):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        passport_path = _save_upload(passport_image, tmp_dir)

        try:
            result = process_passport(str(passport_path))
        except Exception as exc:  # noqa: BLE001 - surfaced as 422 below
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"OCR pipeline failed: {exc}",
            ) from exc

        return _to_ocr_result(result)


@router.post(
    "/tamper-check",
    response_model=TamperingAnalysisResult,
    summary="Run forensic tampering screening on a document image (Module 3 only)",
)
async def tamper_check(passport_image: UploadFile = File(...)):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        passport_path = _save_upload(passport_image, tmp_dir)

        try:
            result = detect_tampering(str(passport_path))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Tampering analysis failed: {exc}",
            ) from exc

        return TamperingAnalysisResult(**result)


@router.post(
    "/verify",
    response_model=PassportVerificationResponse,
    summary=(
        "Full pipeline: document validation + tampering screening + OCR/MRZ "
        "(+ visible-field consistency) + face match against a selfie"
    ),
)
async def verify_passport(
    passport_image: UploadFile = File(...),
    selfie_image: Optional[UploadFile] = File(
        None, description="Live selfie to match against the passport photo. Optional."
    ),
    current_user: dict = Depends(get_current_user),
):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        passport_path = _save_upload(passport_image, tmp_dir)

        # ------------------------------------------------------
        # Module 2 — Document validation (stubbed for now)
        # ------------------------------------------------------
        doc_result = validate_document(str(passport_path))

        # ------------------------------------------------------
        # Module 3 — Tampering / forensics screening
        # ------------------------------------------------------
        try:
            tampering_raw = detect_tampering(str(passport_path))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Tampering analysis failed: {exc}",
            ) from exc

        tampering_result = TamperingAnalysisResult(**tampering_raw)

        # ------------------------------------------------------
        # Module 1 — OCR + MRZ
        # ------------------------------------------------------
        try:
            ocr_raw = process_passport(str(passport_path))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"OCR pipeline failed: {exc}",
            ) from exc

        structure = ocr_raw.get("structureValidation", {}) or {}
        mrz_valid = structure.get("valid", False)
        ocr_result = _to_ocr_result(ocr_raw)

        # ------------------------------------------------------
        # Module 1b — Visible-field OCR + MRZ consistency check
        #
        # Best-effort: the visible-field region crops are calibrated
        # to a specific passport layout, so on documents that don't
        # match it this can legitimately fail. That's treated as
        # "not available" rather than a hard verification failure —
        # it's an extra consistency signal on top of MRZ validation,
        # not a replacement for it.
        # ------------------------------------------------------
        visible_fields_result = None
        field_consistency_result = None

        try:
            visible_raw = extract_visible_fields(str(passport_path))
            visible_fields_result = VisiblePassportFields(
                passportNumber=visible_raw.get("passportNumber"),
                nationality=visible_raw.get("nationality"),
                dob=visible_raw.get("dob"),
                expiry=visible_raw.get("expiry"),
                sex=visible_raw.get("sex"),
            )

            consistency_raw = compare_visible_to_mrz(visible_raw, ocr_raw)
            field_consistency_result = FieldConsistencyResult(**consistency_raw)
        except Exception:  # noqa: BLE001
            # Non-fatal: leave both fields as None in the response.
            pass

        # ------------------------------------------------------
        # Module 4 — Face detection + match (only if a selfie was sent)
        # ------------------------------------------------------
        face_match_result = None
        face_match_ok = True  # doesn't block verification if no selfie given

        if selfie_image is not None:
            selfie_path = _save_upload(selfie_image, tmp_dir)

            try:
                faces = detect_faces(str(passport_path))
                if not faces:
                    raise ValueError("No face detected in passport image.")

                cropped_face_path = tmp_dir / "passport_face.png"
                crop_passport_face(
                    str(passport_path), faces, str(cropped_face_path)
                )

                face_result = compare_faces(
                    str(cropped_face_path), str(selfie_path)
                )
            except Exception as exc:  # noqa: BLE001
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Face verification failed: {exc}",
                ) from exc

            face_match_result = FaceMatchResult(
                similarity=face_result["similarity"],
                threshold=face_result["threshold"],
                matched=face_result["matched"],
            )
            face_match_ok = face_match_result.matched

        tampering_ok = tampering_result.status not in TAMPERING_BLOCKING_STATUSES

        verified = bool(
            mrz_valid
            and face_match_ok
            and doc_result["valid"]
            and tampering_ok
        )

        response = PassportVerificationResponse(
            ocr=ocr_result,
            faceMatch=face_match_result,
            documentValidation=DocumentValidationResult(**doc_result),
            tamperingAnalysis=tampering_result,
            visibleFields=visible_fields_result,
            fieldConsistency=field_consistency_result,
            verified=verified,
        )

        # ------------------------------------------------------
        # Persist this screening to history so it shows up on the
        # dashboard / history page and can be re-opened later.
        # ------------------------------------------------------
        score, risk = compute_score(response.model_dump())
        name = f"{ocr_result.givenNames or ''} {ocr_result.surname or ''}".strip() or None

        history_doc = {
            "officerId": str(current_user["_id"]),
            "officerName": current_user["name"],
            "createdAt": datetime.now(timezone.utc),
            "documentType": "Passport",
            "passportNumber": ocr_result.passportNumber,
            "name": name,
            "nationality": ocr_result.nationality,
            "verified": verified,
            "score": score,
            "risk": risk,
            "result": response.model_dump(),
        }
        insert_result = await scan_history_collection.insert_one(history_doc)
        response.historyId = str(insert_result.inserted_id)

        return response


def _to_summary(doc: dict) -> ScanHistorySummary:
    return ScanHistorySummary(
        id=str(doc["_id"]),
        createdAt=doc["createdAt"].isoformat(),
        documentType=doc.get("documentType", "Passport"),
        passportNumber=doc.get("passportNumber"),
        name=doc.get("name"),
        nationality=doc.get("nationality"),
        officerName=doc.get("officerName", "Unknown"),
        verified=doc.get("verified", False),
        score=doc.get("score", 0),
        risk=doc.get("risk", "HIGH"),
    )


@router.get(
    "/history",
    response_model=list[ScanHistorySummary],
    summary="List past screenings, most recent first",
)
async def list_history(
    limit: int = 50,
    skip: int = 0,
    current_user: dict = Depends(get_current_user),  # noqa: ARG001 - auth required, shared visibility
):
    cursor = (
        scan_history_collection.find()
        .sort("createdAt", -1)
        .skip(max(skip, 0))
        .limit(min(max(limit, 1), 200))
    )
    docs = await cursor.to_list(length=None)
    return [_to_summary(doc) for doc in docs]


@router.get(
    "/history/{history_id}",
    response_model=ScanHistoryDetail,
    summary="Fetch the full stored result for one past screening",
)
async def get_history_detail(
    history_id: str,
    current_user: dict = Depends(get_current_user),  # noqa: ARG001
):
    try:
        object_id = ObjectId(history_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found.")

    doc = await scan_history_collection.find_one({"_id": object_id})
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found.")

    summary = _to_summary(doc)
    return ScanHistoryDetail(**summary.model_dump(), result=doc["result"])
