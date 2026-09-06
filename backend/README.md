# VERIDEX

ML/AI verification engine for SIHVerify.AI — OCR/MRZ extraction, document
validation, tampering detection, and face-match verification for identity
documents, exposed over a FastAPI HTTP layer.

## Structure

```
VERIDEX/
├── app/                       # FastAPI layer (HTTP only, no ML logic)
│   ├── main.py                 entrypoint — `uvicorn app.main:app`
│   ├── schemas.py               Pydantic request/response models
│   └── routers/
│       ├── health.py            GET /health
│       └── passport.py          POST /api/v1/passport/ocr, /verify
│
├── ai_service/                # ML/CV pipeline (framework-agnostic, plain dicts)
│   ├── config.py                model paths, tesseract path, thresholds — env-overridable
│   ├── ocr/                     Module 1: OCR + MRZ extraction
│   │   ├── preprocess.py         crop the MRZ strip
│   │   ├── extractor.py          orchestrator: OCR -> parse -> validate
│   │   ├── corrections.py        single source of truth for the OCR
│   │   │                         digit-confusion map (was duplicated 3x)
│   │   ├── mrz_normalizer.py     live pipeline normalizer (uses corrections.py)
│   │   ├── mrz_corrector.py      experimental alt. corrector (uses corrections.py)
│   │   ├── mrz_candidate.py      experimental field/confidence scorer
│   │   ├── mrz_parser.py         ICAO TD3 parser (names, dates, check digits)
│   │   ├── mrz_validator.py      structural/date/check-digit validation
│   │   ├── visible_extractor.py  [NEW] OCR of the visible (non-MRZ) printed
│   │   │                         fields — passport #, nationality, DOB, expiry, sex
│   │   └── field_validator.py    [NEW] cross-checks visible fields vs. parsed MRZ,
│   │                             returns a consistency score + status
│   ├── face/                    Module 4: face detection + matching
│   │   ├── detector.py           MediaPipe face detection
│   │   ├── cropper.py            passport-portrait crop
│   │   └── recognizer.py         OpenCV SFace embeddings + cosine similarity
│   ├── document/                Module 2: document validation — STUB, not implemented
│   │   └── detector.py
│   └── tampering/               [NEW] Module 3: image forensics / tampering screening
│       ├── detector.py           orchestrator — combines all checks below into
│       │                         one tamperingScore + status (LOW_RISK / SUSPICIOUS / HIGH_RISK)
│       ├── metadata.py           EXIF metadata analysis (Pillow)
│       ├── stamp_check.py        stamp/seal region detection + manipulation heuristics
│       ├── photo_check.py        photo-replacement heuristics
│       └── text_check.py         text-region manipulation / editing-boundary heuristics
│
├── models/                    # binary model weights (moved out of repo root)
│   ├── face_detector.tflite
│   └── face_recognition_sface_2021dec.onnx
│
├── sample_data/                sample/test images (incl. known-tampered samples)
├── tests/                      standalone test/debug scripts (see note below)
├── requirements.txt
└── .env.example
```

## What changed from the original layout

- Moved `*.tflite` / `*.onnx` model weights out of the repo root into `models/`.
- Moved sample/test images into `sample_data/`.
- Moved all `test_*.py` scripts into `tests/` (they're standalone `print`-based
  scripts, not a pytest suite — run them individually **from the `backend/`
  root**, e.g. `python tests/test_passport_verification.py` — the sample-data
  paths inside them are relative to `backend/`, not to `tests/`).
- Added `ai_service/config.py` so model paths and the Tesseract binary path
  are resolved via environment variables instead of hardcoded
  (the old code hardcoded a **Windows-only** `C:\Program Files\Tesseract-OCR\...`
  path and bare relative filenames like `"face_detector.tflite"` that only
  worked if the process happened to be launched from inside `VERIDEX/`).
- Consolidated the OCR digit-confusion map, which was copy-pasted identically
  across `mrz_normalizer.py`, `mrz_corrector.py`, and `mrz_candidate.py`, into
  one shared `ai_service/ocr/corrections.py`. All three now import from it;
  public function names are unchanged so nothing else needed to change.
- Added the `app/` FastAPI layer, wired to the existing `ai_service` functions
  without modifying their internals.
- Added `requirements.txt` and `.env.example` (neither existed before).
- **Merged in Module 3 (Tampering Detection)** from the standalone VERIDEX dev
  repo: `ai_service/tampering/` (metadata / stamp / photo / text forensic
  checks, combined into one `tamperingScore` + `status`), plus the visible-field
  OCR + MRZ consistency check (`ocr/visible_extractor.py`, `ocr/field_validator.py`).
  `visible_extractor.py` was updated to resolve Tesseract via `ai_service.config`
  instead of a hardcoded Windows path, matching the rest of the OCR pipeline.
  `/api/v1/passport/verify` now runs all of this and folds a `HIGH_RISK`
  tampering verdict into the final `verified` boolean; a standalone
  `/api/v1/passport/tamper-check` endpoint was added to run Module 3 in isolation.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

# Linux/Debian also needs the tesseract binary itself:
sudo apt-get install tesseract-ocr

# macOS:
brew install tesseract
```

On Windows, if `tesseract` isn't on PATH, set `VERIDEX_TESSERACT_CMD` in a
`.env` file (see `.env.example`) to the full path of `tesseract.exe`.

## Run the API

```bash
uvicorn app.main:app --reload --port 8000
```

Then open **http://127.0.0.1:8000/docs** for interactive Swagger UI.

### Endpoints

| Method | Path                          | Description                                              |
|--------|-------------------------------|------------------------------------------------------------|
| GET    | `/health`                     | Liveness check                                              |
| POST   | `/api/v1/passport/ocr`        | Upload a passport image, get back OCR + MRZ fields (Module 1) |
| POST   | `/api/v1/passport/tamper-check` | Upload a document image, get back a forensic tampering analysis (Module 3, standalone) |
| POST   | `/api/v1/passport/verify`     | Upload a passport image (+ optional selfie); runs document validation (stub) + tampering screening + OCR/MRZ + visible-field consistency + face match, returns a combined `verified` boolean |

### Example requests

```bash
curl -X POST http://127.0.0.1:8000/api/v1/passport/verify \
  -F "passport_image=@sample_data/passport_test.png;type=image/png" \
  -F "selfie_image=@sample_data/user_face.png;type=image/png"

curl -X POST http://127.0.0.1:8000/api/v1/passport/tamper-check \
  -F "passport_image=@sample_data/passport_stamp_tampered.png;type=image/png"
```

## Known limitations / next steps

- **Module 2 (Document Validation)** is still not implemented.
  `ai_service/document/detector.py` defines the expected function contract
  (`validate_document`) so the API layer already calls it — only that file
  needs to change once it's built.
- **Module 3 (Tampering Detection)** is a heuristic forensic screen (EXIF
  metadata, stamp/seal, photo-replacement, and text-manipulation checks). A
  `SUSPICIOUS` or `HIGH_RISK` result flags a document for review — it does not
  by itself prove forgery. Only `HIGH_RISK` currently blocks `verified` in
  `/verify`; tune `TAMPERING_BLOCKING_STATUSES` in `app/routers/passport.py`
  if `SUSPICIOUS` should block too.
- `ai_service/ocr/visible_extractor.py`'s field regions are calibrated to one
  test passport layout (ratios hardcoded per field). On other layouts it will
  legitimately fail — `/verify` treats that as "consistency check unavailable"
  rather than a hard failure, so it never blocks verification on its own.
- The face-match threshold (`0.363`) is an initial development guess, not
  calibrated against a labeled dataset yet — see `VERIDEX_FACE_MATCH_THRESHOLD`
  in `.env.example`.
- The 37 MB SFace `.onnx` model is committed directly to the repo. Consider
  Git LFS, or downloading it at build/deploy time, if repo size becomes a
  problem.
- `tests/` scripts are ad hoc, not `pytest`-discoverable assertions — fine for
  local debugging, but worth converting to real `pytest` tests (with
  `TestClient` for the API layer) before CI is set up.
