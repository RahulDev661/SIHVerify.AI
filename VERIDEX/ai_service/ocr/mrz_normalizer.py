import re


DIGIT_CORRECTIONS = {
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


def clean_ocr_mrz(text: str) -> str:
    """Remove spaces and invalid MRZ characters."""

    text = text.upper()

    text = re.sub(
        r"[^A-Z0-9<]",
        "",
        text
    )

    return text


def correct_digit_field(text: str) -> str:
    """
    Apply OCR corrections ONLY to a field
    that should contain digits.
    """

    result = ""

    for char in text:

        if char.isdigit():
            result += char

        elif char in DIGIT_CORRECTIONS:
            result += DIGIT_CORRECTIONS[char]

        else:
            result += char

    return result


def correct_check_digit(char: str) -> str:
    """Correct a single MRZ check digit."""

    if char.isdigit():
        return char

    return DIGIT_CORRECTIONS.get(
        char,
        char
    )


def normalize_mrz_line1(line: str) -> str:

    line = clean_ocr_mrz(line)

    return line


def normalize_mrz_line2(line: str) -> str:
    """
    Normalize TD3 passport MRZ line 2.

    0-8   passport number
    9     passport check digit
    10-12 nationality
    13-18 DOB
    19    DOB check digit
    20    sex
    21-26 expiry
    27    expiry check digit
    """

    line = clean_ocr_mrz(line)

    if len(line) < 28:
        return line

    chars = list(line)

    # -----------------------------------------
    # PASSPORT NUMBER
    # -----------------------------------------
    # DO NOT modify it yet.
    # Passport numbers contain letters and digits.

    # -----------------------------------------
    # PASSPORT CHECK DIGIT
    # -----------------------------------------

    chars[9] = correct_check_digit(
        chars[9]
    )

    # -----------------------------------------
    # NATIONALITY
    # -----------------------------------------
    # IMPORTANT:
    # DO NOT modify positions 10-12.

    # -----------------------------------------
    # DATE OF BIRTH
    # -----------------------------------------

    chars[13:19] = list(
        correct_digit_field(
            "".join(chars[13:19])
        )
    )

    # -----------------------------------------
    # DOB CHECK DIGIT
    # -----------------------------------------

    chars[19] = correct_check_digit(
        chars[19]
    )

    # -----------------------------------------
    # SEX
    # -----------------------------------------
    # Leave unchanged.

    # -----------------------------------------
    # EXPIRY DATE
    # -----------------------------------------

    chars[21:27] = list(
        correct_digit_field(
            "".join(chars[21:27])
        )
    )

    # -----------------------------------------
    # EXPIRY CHECK DIGIT
    # -----------------------------------------

    chars[27] = correct_check_digit(
        chars[27]
    )

    return "".join(chars)


def normalize_mrz_lines(
    line1: str,
    line2: str
):

    return (
        normalize_mrz_line1(line1),
        normalize_mrz_line2(line2)
    )