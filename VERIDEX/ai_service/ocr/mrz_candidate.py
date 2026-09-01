import re

from .mrz_parser import calculate_check_digit


# --------------------------------------------------
# COMMON OCR CONFUSIONS
# --------------------------------------------------

OCR_TO_DIGIT = {
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


# --------------------------------------------------
# BASIC CHARACTER HELPERS
# --------------------------------------------------

def ocr_to_digit(char: str) -> str:
    """
    Convert a character that looks like a digit
    into a digit.

    Example:
        O -> 0
        I -> 1
        L -> 1
    """

    char = char.upper()

    if char.isdigit():
        return char

    return OCR_TO_DIGIT.get(char, char)


def clean_mrz_text(text: str) -> str:
    """
    Keep only characters that can occur in MRZ text.
    """

    text = text.upper()

    return re.sub(
        r"[^A-Z0-9<]",
        "",
        text
    )


# --------------------------------------------------
# FIELD VALIDATORS
# --------------------------------------------------

def is_valid_date(value: str) -> bool:
    """
    Check whether a field looks like YYMMDD.
    """

    if len(value) != 6:
        return False

    if not value.isdigit():
        return False

    month = int(value[2:4])
    day = int(value[4:6])

    if month < 1 or month > 12:
        return False

    if day < 1 or day > 31:
        return False

    return True


def is_valid_sex(value: str) -> bool:
    """
    Valid TD3 sex values.
    """

    return value in (
        "M",
        "F",
        "<"
    )


def is_valid_nationality(value: str) -> bool:
    """
    Basic MRZ nationality validation.

    Nationality should contain exactly
    three alphabetic characters.
    """

    return bool(
        re.fullmatch(
            r"[A-Z]{3}",
            value
        )
    )


# --------------------------------------------------
# CHECK DIGIT VALIDATION
# --------------------------------------------------

def validate_check_digit(
    field: str,
    check_digit: str
) -> bool:

    check_digit = ocr_to_digit(
        check_digit
    )

    if not check_digit.isdigit():
        return False

    calculated = calculate_check_digit(
        field
    )

    return calculated == int(
        check_digit
    )


# --------------------------------------------------
# FIXED POSITION EXTRACTION
# --------------------------------------------------

def extract_td3_fields(line2: str) -> dict:
    """
    Extract fields according to the official
    44-character TD3 passport layout.
    """

    line2 = line2[:44].ljust(
        44,
        "<"
    )

    return {
        "passportNumber": line2[0:9],

        "passportCheckDigit": line2[9],

        "nationality": line2[10:13],

        "dob": line2[13:19],

        "dobCheckDigit": line2[19],

        "sex": line2[20],

        "expiry": line2[21:27],

        "expiryCheckDigit": line2[27],

        "optionalData": line2[28:44]
    }


# --------------------------------------------------
# POSITION-AWARE NORMALIZATION
# --------------------------------------------------

def normalize_td3_line2(line2: str) -> str:
    """
    Normalize a 44-character OCR line according
    to the TD3 structure.

    IMPORTANT:
    This does NOT shift characters.

    It only fixes characters where the field
    type is known.
    """

    line2 = clean_mrz_text(
        line2
    )

    line2 = line2[:44].ljust(
        44,
        "<"
    )

    chars = list(line2)

    # ------------------------------------------
    # NUMERIC FIELDS
    # ------------------------------------------

    # DOB positions: 13-18
    for i in range(13, 19):

        chars[i] = ocr_to_digit(
            chars[i]
        )

    # Expiry positions: 21-26
    for i in range(21, 27):

        chars[i] = ocr_to_digit(
            chars[i]
        )

    # Check digits
    for i in (
        9,
        19,
        27
    ):

        chars[i] = ocr_to_digit(
            chars[i]
        )

    return "".join(chars)


# --------------------------------------------------
# STRUCTURE ANALYSIS
# --------------------------------------------------

def analyze_td3_line2(line2: str) -> dict:
    """
    Analyze a possible TD3 MRZ line.
    """

    line2 = normalize_td3_line2(
        line2
    )

    fields = extract_td3_fields(
        line2
    )

    errors = []

    # ------------------------------------------
    # PASSPORT NUMBER
    # ------------------------------------------

    if not re.fullmatch(
        r"[A-Z0-9<]{9}",
        fields["passportNumber"]
    ):
        errors.append(
            "Invalid passport number field."
        )

    # ------------------------------------------
    # NATIONALITY
    # ------------------------------------------

    if not is_valid_nationality(
        fields["nationality"]
    ):
        errors.append(
            "Invalid nationality."
        )

    # ------------------------------------------
    # DOB
    # ------------------------------------------

    if not is_valid_date(
        fields["dob"]
    ):
        errors.append(
            "Invalid date of birth field."
        )

    # ------------------------------------------
    # SEX
    # ------------------------------------------

    if not is_valid_sex(
        fields["sex"]
    ):
        errors.append(
            "Invalid sex field."
        )

    # ------------------------------------------
    # EXPIRY
    # ------------------------------------------

    if not is_valid_date(
        fields["expiry"]
    ):
        errors.append(
            "Invalid expiry date field."
        )

    # ------------------------------------------
    # CHECK DIGITS
    # ------------------------------------------

    passport_valid = validate_check_digit(
        fields["passportNumber"],
        fields["passportCheckDigit"]
    )

    dob_valid = validate_check_digit(
        fields["dob"],
        fields["dobCheckDigit"]
    )

    expiry_valid = validate_check_digit(
        fields["expiry"],
        fields["expiryCheckDigit"]
    )

    # ------------------------------------------
    # RESULT
    # ------------------------------------------

    return {
        "line": line2,

        "fields": fields,

        "structureValid": len(errors) == 0,

        "errors": errors,

        "checkDigits": {
            "passportNumber": passport_valid,
            "dateOfBirth": dob_valid,
            "expiry": expiry_valid
        }
    }


# --------------------------------------------------
# CONFIDENCE
# --------------------------------------------------

def calculate_confidence(
    analysis: dict
) -> float:

    score = 0.0

    # Structure
    if analysis["structureValid"]:
        score += 0.4

    # Check digits
    checks = analysis["checkDigits"]

    if checks["passportNumber"]:
        score += 0.2

    if checks["dateOfBirth"]:
        score += 0.2

    if checks["expiry"]:
        score += 0.2

    return score


# --------------------------------------------------
# MAIN CORRECTION FUNCTION
# --------------------------------------------------

def correct_mrz_line2(
    ocr_line: str
) -> dict:

    normalized = normalize_td3_line2(
        ocr_line
    )

    analysis = analyze_td3_line2(
        normalized
    )

    confidence = calculate_confidence(
        analysis
    )

    return {
        "original": ocr_line,

        "normalized": normalized,

        "confidence": confidence,

        "verified": confidence >= 0.8,

        "analysis": analysis
    }