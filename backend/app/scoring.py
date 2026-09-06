"""
Shared score/risk heuristic.

Mirrors the frontend's `computeScore` (frontend/src/pages/result.jsx) so
the score stored with a history record matches what the officer saw at
scan time. Kept in one place so the two never drift apart silently —
if you change the weighting, update both.
"""

from typing import Any


def compute_score(result: dict[str, Any]) -> tuple[int, str]:
    score = 100

    ocr = result.get("ocr") or {}
    mrz_valid = (ocr.get("structureValidation") or {}).get("valid", False)
    if not mrz_valid:
        score -= 40

    doc_validation = result.get("documentValidation")
    if doc_validation and not doc_validation.get("valid", True):
        score -= 30

    face_match = result.get("faceMatch")
    if face_match and not face_match.get("matched", True):
        score -= 30

    score = max(0, min(100, score))

    if score >= 80:
        risk = "LOW"
    elif score >= 50:
        risk = "MEDIUM"
    else:
        risk = "HIGH"

    return score, risk
