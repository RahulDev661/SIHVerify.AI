import re


def clean_mrz_line(line: str) -> str:
    """Clean an MRZ line."""

    line = line.upper().strip()

    # Keep only valid MRZ characters
    line = re.sub(r"[^A-Z0-9<]", "", line)

    return line


def is_possible_mrz_line(line: str) -> bool:
    """Check whether a line looks like an MRZ line."""

    line = clean_mrz_line(line)

    if len(line) < 30:
        return False

    return line.count("<") >= 2


def find_mrz_lines(text: str) -> list:
    """
    Find possible passport MRZ lines from OCR text.

    A standard passport MRZ contains two lines,
    normally 44 characters each.
    """

    lines = text.splitlines()

    candidates = []

    for line in lines:

        cleaned = clean_mrz_line(line)

        # MRZ lines should be reasonably long
        if len(cleaned) >= 30:

            # Passport MRZ normally contains '<'
            if "<" in cleaned:

                candidates.append(cleaned)

    return candidates

# --------------------------------------------------
# MRZ CHECK DIGIT
# --------------------------------------------------

def calculate_check_digit(data: str) -> int:
    """
    Calculate ICAO MRZ check digit.

    Character values:
        0-9 -> 0-9
        A-Z -> 10-35
        <   -> 0

    Weights:
        7, 3, 1 repeating
    """

    weights = [7, 3, 1]

    total = 0

    for index, char in enumerate(data):

        if char == "<":
            value = 0

        elif char.isdigit():
            value = int(char)

        elif "A" <= char <= "Z":
            value = ord(char) - ord("A") + 10

        else:
            value = 0

        total += value * weights[index % 3]

    return total % 10


# --------------------------------------------------
# DATE CONVERSION
# --------------------------------------------------

def convert_mrz_date(date: str) -> str:
    """
    Convert YYMMDD into DD/MM/YYYY.

    MRZ stores years using two digits.
    For this prototype, dates from 00-49
    are treated as 2000-2049 and dates
    from 50-99 as 1950-1999.
    """

    if len(date) != 6 or not date.isdigit():
        return date

    yy = int(date[0:2])
    mm = date[2:4]
    dd = date[4:6]

    if yy <= 49:
        year = 2000 + yy
    else:
        year = 1900 + yy

    return f"{dd}/{mm}/{year}"


# --------------------------------------------------
# PASSPORT MRZ PARSER
# --------------------------------------------------

def parse_passport_mrz(line1: str, line2: str) -> dict:
    """
    Parse a standard TD3 passport MRZ.

    TD3 format:

    Line 1:
    P<COUNTRY<SURNAME<<GIVEN<NAMES<<<<<<<<<<<<

    Line 2:
    PASSPORTNUMBER<CNTRY<DOB<CSEXEXPIRY<...
    """

    line1 = clean_mrz_line(line1)
    line2 = clean_mrz_line(line2)

    if len(line1) < 44 or len(line2) < 44:
        raise ValueError(
            "Invalid MRZ: passport MRZ lines should contain 44 characters."
        )

    # Use first 44 characters
    line1 = line1[:44]
    line2 = line2[:44]

    # ------------------------------------------------
    # LINE 1
    # ------------------------------------------------

    document_type = line1[0]

    issuing_country = line1[2:5]

    names_section = line1[5:]

    # Replace filler characters
    names_section = names_section.replace("<", " ")

    names_section = " ".join(names_section.split())

    name_parts = names_section.split("  ")

    if len(name_parts) >= 2:

        surname = name_parts[0].strip()

        given_names = name_parts[1].strip()

    else:

        parts = names_section.split()

        surname = parts[0] if parts else ""

        given_names = " ".join(parts[1:])


    # ------------------------------------------------
    # LINE 2
    # ------------------------------------------------

    passport_number = line2[0:9]

    passport_number_check = line2[9]

    nationality = line2[10:13]

    birth_date = line2[13:19]

    birth_check = line2[19]

    sex = line2[20]

    expiry_date = line2[21:27]

    expiry_check = line2[27]

    # ------------------------------------------------
    # CHECK DIGITS
    # ------------------------------------------------

    passport_number_clean = passport_number.replace("<", "")

    passport_check_valid = (
        calculate_check_digit(passport_number)
        == int(passport_number_check)
    )

    birth_check_valid = (
        calculate_check_digit(birth_date)
        == int(birth_check)
    )

    expiry_check_valid = (
        calculate_check_digit(expiry_date)
        == int(expiry_check)
    )

    return {
        "documentType": document_type,
        "issuingCountry": issuing_country,
        "surname": surname,
        "givenNames": given_names,
        "passportNumber": passport_number_clean,
        "nationality": nationality,
        "dob": convert_mrz_date(birth_date),
        "sex": sex,
        "expiry": convert_mrz_date(expiry_date),
        "validation": {
            "passportNumberCheckDigit": passport_check_valid,
            "dateOfBirthCheckDigit": birth_check_valid,
            "expiryCheckDigit": expiry_check_valid
        }
    }


def parse_mrz_from_ocr(text: str) -> dict:
    """
    Automatically find and parse a passport MRZ
    from OCR text.
    """

    mrz_lines = find_mrz_lines(text)

    if len(mrz_lines) < 2:
        raise ValueError(
            "Could not find two MRZ lines in OCR text."
        )

    # Use the last two likely MRZ lines
    line1 = mrz_lines[-2]
    line2 = mrz_lines[-1]

    # Make sure they are exactly 44 characters
    line1 = line1[:44]
    line2 = line2[:44]

    return parse_passport_mrz(
        line1,
        line2
    )