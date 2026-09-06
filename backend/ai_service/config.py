"""
Central configuration for the VERIDEX ai_service package.

Every path/threshold that used to be hardcoded inside individual
modules (face_detector.tflite, the SFace .onnx model, the Windows
tesseract.exe path, etc.) now lives here and can be overridden with
environment variables — so the same code runs unmodified on Windows,
Linux, and inside a Docker container.
"""

import os
import shutil
from pathlib import Path

# ai_service/config.py -> VERIDEX/
BASE_DIR = Path(__file__).resolve().parent.parent

MODELS_DIR = Path(os.getenv("VERIDEX_MODELS_DIR", BASE_DIR / "models"))

FACE_DETECTOR_MODEL_PATH = Path(
    os.getenv(
        "VERIDEX_FACE_DETECTOR_MODEL",
        MODELS_DIR / "face_detector.tflite",
    )
)

FACE_RECOGNIZER_MODEL_PATH = Path(
    os.getenv(
        "VERIDEX_FACE_RECOGNIZER_MODEL",
        MODELS_DIR / "face_recognition_sface_2021dec.onnx",
    )
)

# --------------------------------------------------------------------
# Tesseract
# --------------------------------------------------------------------
# Only set an explicit binary path if VERIDEX_TESSERACT_CMD is provided
# (e.g. on Windows dev machines). On Linux/Docker, rely on `tesseract`
# being on PATH (installed via apt) and let pytesseract find it.


def resolve_tesseract_cmd() -> str | None:
    env_path = os.getenv("VERIDEX_TESSERACT_CMD")
    if env_path:
        return env_path

    found = shutil.which("tesseract")
    if found:
        return found

    # Common Windows default, kept only as a last-resort fallback.
    windows_default = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if Path(windows_default).exists():
        return windows_default

    return None


TESSERACT_CMD = resolve_tesseract_cmd()

# --------------------------------------------------------------------
# Face matching
# --------------------------------------------------------------------
FACE_MATCH_THRESHOLD = float(os.getenv("VERIDEX_FACE_MATCH_THRESHOLD", "0.363"))
