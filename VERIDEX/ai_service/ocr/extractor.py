import pytesseract

from ai_service.ocr.preprocess import preprocess_mrz
from ai_service.ocr.mrz_normalizer import normalize_mrz_lines
from ai_service.ocr.mrz_parser import parse_passport_mrz
from ai_service.ocr.mrz_validator import validate_mrz_structure


# ==================================================
# TESSERACT
# ==================================================

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


# ==================================================
# MRZ OCR CONFIGURATION
# ==================================================

MRZ_CONFIG = (
    "--oem 3 "
    "--psm 6 "
    "-c tessedit_char_whitelist="
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<"
)


# ==================================================
# CLEAN MRZ CHARACTER
# ==================================================

def clean_mrz_text(text: str) -> str:
    """
    Keep only characters allowed in passport MRZ.
    """

    text = text.upper()

    return "".join(
        c for c in text
        if c.isalnum() or c == "<"
    )


# ==================================================
# EXTRACT MRZ LINES
# ==================================================

def extract_mrz_lines(image_path: str):

    # ----------------------------------------------
    # STEP 1 — PREPROCESS IMAGE
    # ----------------------------------------------

    processed = preprocess_mrz(image_path)

    # ----------------------------------------------
    # STEP 2 — OCR
    # ----------------------------------------------

    text = pytesseract.image_to_string(
        processed,
        config=MRZ_CONFIG
    )

    # ----------------------------------------------
    # DEBUG RAW OCR
    # ----------------------------------------------

    print()
    print("========== RAW MRZ OCR ==========")
    print(text)
    print("==================================")
    print()

    # ----------------------------------------------
    # STEP 3 — FIND CANDIDATE LINES
    # ----------------------------------------------

    candidates = []

    for raw_line in text.splitlines():

        cleaned = clean_mrz_text(raw_line)

        print(
            "OCR candidate:",
            repr(cleaned),
            "Length:",
            len(cleaned)
        )

        # MRZ lines normally contain many characters.
        if len(cleaned) >= 25:

            candidates.append(cleaned)

    # ----------------------------------------------
    # STEP 4 — CHECK TWO LINES
    # ----------------------------------------------

    if len(candidates) < 2:

        raise ValueError(
            "Could not detect two MRZ lines."
        )

    # ----------------------------------------------
    # STEP 5 — TAKE LAST TWO CANDIDATES
    # ----------------------------------------------

    line1 = candidates[-2]
    line2 = candidates[-1]

    # ----------------------------------------------
    # STEP 6 — NORMALIZE LENGTH
    # ----------------------------------------------

    line1 = line1[:44].ljust(44, "<")
    line2 = line2[:44].ljust(44, "<")

    # ----------------------------------------------
    # DEBUG NORMALIZED MRZ
    # ----------------------------------------------

    print()
    print("========== NORMALIZED MRZ OCR ==========")

    print("Line 1:")
    print(line1)

    print("Length:", len(line1))

    print()

    print("Line 2:")
    print(line2)

    print("Length:", len(line2))

    print("=========================================")
    print()

    return line1, line2


# ==================================================
# COMPLETE PASSPORT PIPELINE
# ==================================================

def process_passport(image_path: str) -> dict:

    print()
    print("========================================")
    print("       VERIDEX PASSPORT PIPELINE")
    print("========================================")
    print()

    # ----------------------------------------------
    # STEP 1 — OCR
    # ----------------------------------------------

    line1, line2 = extract_mrz_lines(
        image_path
    )

    # ----------------------------------------------
    # STEP 2 — MRZ NORMALIZATION
    # ----------------------------------------------

    line1, line2 = normalize_mrz_lines(
        line1,
        line2
    )

    # ----------------------------------------------
    # STEP 3 — STRUCTURE VALIDATION
    # ----------------------------------------------

    structure_validation = validate_mrz_structure(
        line1,
        line2
    )

    print()
    print("========== MRZ STRUCTURE ==========")

    print(
        "Valid:",
        structure_validation["valid"]
    )

    if structure_validation["errors"]:

        for error in structure_validation["errors"]:

            print(
                "ERROR:",
                error
            )

    print("====================================")
    print()

    # ----------------------------------------------
    # STEP 4 — PARSE MRZ
    # ----------------------------------------------

    try:

        result = parse_passport_mrz(
            line1,
            line2
        )

    except Exception as e:

        print(
            "MRZ parser error:",
            e
        )

        raise

    # ----------------------------------------------
    # STEP 5 — ADD STRUCTURE VALIDATION
    # ----------------------------------------------

    result["structureValidation"] = (
        structure_validation
    )

    # ----------------------------------------------
    # STEP 6 — ADD RAW MRZ
    # ----------------------------------------------

    result["mrz"] = {

        "line1": line1,

        "line2": line2
    }

    # ----------------------------------------------
    # STEP 7 — RETURN JSON
    # ----------------------------------------------

    return result