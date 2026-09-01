# --------------------------------------------------
# MRZ OCR CORRECTION
# --------------------------------------------------

OCR_DIGIT_MAP = {
    "O": "0",
    "Q": "0",
    "D": "0",

    "I": "1",
    "L": "1",

    "Z": "2",

    "S": "5",

    "G": "6",

    "T": "7",

    "B": "8",
}


def correct_numeric_char(char: str) -> str:
    """
    Convert a common OCR confusion into a digit.

    Only use this function in fields that are
    supposed to contain digits.
    """

    char = char.upper()

    if char.isdigit():
        return char

    return OCR_DIGIT_MAP.get(char, char)


def correct_numeric_field(field: str) -> str:
    """
    Correct OCR characters in a numeric MRZ field.
    """

    return "".join(
        correct_numeric_char(char)
        for char in field
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