# --------------------------------------------------
# MRZ OCR CORRECTION
# --------------------------------------------------
# Confusion map + core helpers now live in ai_service.ocr.corrections
# (previously duplicated here, in mrz_normalizer.py, and in
# mrz_candidate.py).

from ai_service.ocr.corrections import (
    OCR_TO_DIGIT as OCR_DIGIT_MAP,  # kept as alias for back-compat
    correct_char_to_digit as correct_numeric_char,
    correct_digit_field as correct_numeric_field,
)


def correct_mrz_line2(line2: str) -> str:
    """
    Apply position-aware OCR correction to a
    TD3 passport MRZ line.

    IMPORTANT:
    This function does not change the length
    or shift characters.
    """

    line2 = line2.upper()

    # Make exactly 44 characters
    line2 = line2[:44].ljust(44, "<")

    # ------------------------------------------
    # PASSPORT NUMBER
    # ------------------------------------------

    passport_number = line2[0:9]

    # ------------------------------------------
    # PASSPORT CHECK DIGIT
    # ------------------------------------------

    passport_check = line2[9]

    passport_check = correct_numeric_char(
        passport_check
    )

    # ------------------------------------------
    # NATIONALITY
    # ------------------------------------------

    nationality = line2[10:13]

    # ------------------------------------------
    # DOB
    # ------------------------------------------

    dob = correct_numeric_field(
        line2[13:19]
    )

    # ------------------------------------------
    # DOB CHECK DIGIT
    # ------------------------------------------

    dob_check = correct_numeric_char(
        line2[19]
    )

    # ------------------------------------------
    # SEX
    # ------------------------------------------

    sex = line2[20]

    if sex not in ("M", "F", "<"):

        if sex in ("N", "H"):
            sex = "M"

    # ------------------------------------------
    # EXPIRY
    # ------------------------------------------

    expiry = correct_numeric_field(
        line2[21:27]
    )

    # ------------------------------------------
    # EXPIRY CHECK DIGIT
    # ------------------------------------------

    expiry_check = correct_numeric_char(
        line2[27]
    )

    # ------------------------------------------
    # REMAINING MRZ
    # ------------------------------------------

    remaining = line2[28:44]

    # ------------------------------------------
    # REBUILD
    # ------------------------------------------

    corrected = (
        passport_number
        + passport_check
        + nationality
        + dob
        + dob_check
        + sex
        + expiry
        + expiry_check
        + remaining
    )

    return corrected[:44]