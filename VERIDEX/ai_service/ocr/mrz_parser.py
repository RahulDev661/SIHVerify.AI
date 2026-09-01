import re


# ==================================================
# CLEAN MRZ LINE
# ==================================================

def clean_mrz_line(line: str) -> str:
    """
    Clean an OCR MRZ line.

    Keeps only:
        A-Z
        0-9
        <
    """

    line = line.upper().strip()

    line = re.sub(
        r"[^A-Z0-9<]",
        "",
        line
    )

    return line


# ==================================================
# POSSIBLE MRZ LINE
# ==================================================

def is_possible_mrz_line(line: str) -> bool:
    """
    Check whether a line looks like an MRZ line.
    """

    line = clean_mrz_line(line)

    if len(line) < 30:
        return False

    return line.count("<") >= 2


# ==================================================
# FIND MRZ LINES
# ==================================================

def find_mrz_lines(text: str) -> list:
    """
    Find possible passport MRZ lines from OCR text.

    TD3 passport MRZ:
        2 lines
        44 characters per line
    """

    lines = text.splitlines()

    candidates = []

    for line in lines:

        cleaned = clean_mrz_line(line)

        if len(cleaned) >= 30 and "<" in cleaned:

            candidates.append(cleaned)

    return candidates


# ==================================================
# MRZ CHECK DIGIT
# ==================================================

def calculate_check_digit(data: str) -> int:
    """
    Calculate ICAO MRZ check digit.

    Character values:

        0-9 -> 0-9
        A-Z -> 10-35
        <   -> 0

    Repeating weights:

        7, 3, 1
    """

    weights = [7, 3, 1]

    total = 0

    for index, char in enumerate(data):

        if char == "<":

            value = 0

        elif char.isdigit():

            value = int(char)

        elif "A" <= char <= "Z":

            value = (
                ord(char)
                - ord("A")
                + 10
            )

        else:

            value = 0

        total += (
            value
            * weights[index % 3]
        )

    return total % 10


# ==================================================
# DATE CONVERSION
# ==================================================

def convert_mrz_date(date: str) -> str:
    """
    Convert YYMMDD into DD/MM/YYYY.

    Prototype rule:

        00-49 -> 2000-2049
        50-99 -> 1950-1999
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


# ==================================================
# NORMALIZE MRZ NAME
# ==================================================

def parse_mrz_name(names_section: str):
    """
    Extract surname and given names from
    the passport MRZ name section.

    Standard format:

        SURNAME<<GIVEN<NAMES

    Example:

        ORNEK<<MEHMET

    OCR sometimes produces:

        ORNEK<X<MEHMET

    or:

        ORNEK<MEHMET

    Therefore this function handles
    common OCR separator errors.
    """

    # ----------------------------------------------
    # Standard separator
    # ----------------------------------------------

    if "<<" in names_section:

        surname_part, given_part = (
            names_section.split(
                "<<",
                1
            )
        )

    else:

        # ------------------------------------------
        # OCR may convert << into <X<
        # ------------------------------------------

        match = re.search(
            r"<X<",
            names_section
        )

        if match:

            surname_part = (
                names_section[
                    :match.start()
                ]
            )

            given_part = (
                names_section[
                    match.end():
                ]
            )

        else:

            # --------------------------------------
            # OCR fallback
            # --------------------------------------

            parts = names_section.split("<")

            parts = [
                part
                for part in parts
                if part
            ]

            if not parts:

                return "", ""

            surname_part = parts[0]

            given_part = "<".join(
                parts[1:]
            )

    # ----------------------------------------------
    # Clean surname
    # ----------------------------------------------

    surname = surname_part.replace(
        "<",
        " "
    )

    surname = " ".join(
        surname.split()
    )

    # ----------------------------------------------
    # Clean given names
    # ----------------------------------------------

    given_names = given_part.replace(
        "<",
        " "
    )

    given_names = " ".join(
        given_names.split()
    )

    return surname, given_names


# ==================================================
# PASSPORT MRZ PARSER
# ==================================================

def parse_passport_mrz(
    line1: str,
    line2: str
) -> dict:
    """
    Parse a standard TD3 passport MRZ.

    LINE 1:

        P<COUNTRY<SURNAME<<GIVEN<NAMES<<<<<<<<

    LINE 2:

        PASSPORTNUMBER<CNTRY<DOB<CSEXEXPIRY<...
    """

    # ==================================================
    # CLEAN
    # ==================================================

    line1 = clean_mrz_line(line1)

    line2 = clean_mrz_line(line2)

    # ==================================================
    # LENGTH CHECK
    # ==================================================

    if len(line1) < 44:

        raise ValueError(
            "Invalid MRZ: line 1 must contain "
            "at least 44 characters."
        )

    if len(line2) < 44:

        raise ValueError(
            "Invalid MRZ: line 2 must contain "
            "at least 44 characters."
        )

    # Use exactly 44 characters

    line1 = line1[:44]

    line2 = line2[:44]

    # ==================================================
    # LINE 1
    # ==================================================

    document_type = line1[0]

    # Normally:
    #
    # P<
    #
    # positions:
    # 0 = P
    # 1 = <
    # 2-4 = country

    issuing_country = line1[2:5]

    # ----------------------------------------------
    # NAME SECTION
    # ----------------------------------------------

    names_section = line1[5:]

    surname, given_names = parse_mrz_name(
        names_section
    )

    # ==================================================
    # LINE 2
    # ==================================================

    passport_number = line2[0:9]

    passport_number_check = line2[9]

    nationality = line2[10:13]

    birth_date = line2[13:19]

    birth_check = line2[19]

    sex = line2[20]

    expiry_date = line2[21:27]

    expiry_check = line2[27]

    # ==================================================
    # CHECK DIGITS
    # ==================================================

    passport_number_clean = (
        passport_number.replace(
            "<",
            ""
        )
    )

    # ----------------------------------------------
    # Passport number check
    # ----------------------------------------------

    if passport_number_check.isdigit():

        passport_check_valid = (
            calculate_check_digit(
                passport_number
            )
            == int(
                passport_number_check
            )
        )

    else:

        passport_check_valid = False

    # ----------------------------------------------
    # Date of birth check
    # ----------------------------------------------

    if birth_check.isdigit():

        birth_check_valid = (
            calculate_check_digit(
                birth_date
            )
            == int(
                birth_check
            )
        )

    else:

        birth_check_valid = False

    # ----------------------------------------------
    # Expiry check
    # ----------------------------------------------

    if expiry_check.isdigit():

        expiry_check_valid = (
            calculate_check_digit(
                expiry_date
            )
            == int(
                expiry_check
            )
        )

    else:

        expiry_check_valid = False

    # ==================================================
    # RESULT
    # ==================================================

    return {

        "documentType":
            document_type,

        "issuingCountry":
            issuing_country,

        "surname":
            surname,

        "givenNames":
            given_names,

        "passportNumber":
            passport_number_clean,

        "nationality":
            nationality,

        "dob":
            convert_mrz_date(
                birth_date
            ),

        "sex":
            sex,

        "expiry":
            convert_mrz_date(
                expiry_date
            ),

        "validation": {

            "passportNumberCheckDigit":
                passport_check_valid,

            "dateOfBirthCheckDigit":
                birth_check_valid,

            "expiryCheckDigit":
                expiry_check_valid
        }
    }


# ==================================================
# PARSE MRZ FROM OCR
# ==================================================

def parse_mrz_from_ocr(text: str) -> dict:
    """
    Automatically find and parse a passport MRZ
    from OCR text.
    """

    mrz_lines = find_mrz_lines(
        text
    )

    # ==================================================
    # NEED TWO LINES
    # ==================================================

    if len(mrz_lines) < 2:

        raise ValueError(
            "Could not find two MRZ lines "
            "in OCR text."
        )

    # ==================================================
    # USE LAST TWO LIKELY MRZ LINES
    # ==================================================

    line1 = mrz_lines[-2]

    line2 = mrz_lines[-1]

    # ==================================================
    # NORMALIZE LENGTH
    # ==================================================

    line1 = line1[:44]

    line2 = line2[:44]

    # ==================================================
    # PARSE
    # ==================================================

    return parse_passport_mrz(
        line1,
        line2
    )