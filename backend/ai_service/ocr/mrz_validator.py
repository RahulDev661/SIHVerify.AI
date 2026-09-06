from datetime import datetime
import re


# ==================================================
# MRZ CHARACTER VALIDATION
# ==================================================

def validate_characters(line, line_number):
    """
    Check that an MRZ line contains only valid
    ICAO MRZ characters.
    """

    errors = []

    allowed_pattern = r"^[A-Z0-9<]+$"

    if not re.match(allowed_pattern, line):
        errors.append(
            f"Line {line_number} contains invalid MRZ characters."
        )

    return errors


# ==================================================
# DATE VALIDATION
# ==================================================

def validate_date(date_string, field_name):
    """
    Validate YYMMDD date format and ensure that
    the date actually exists.
    """

    errors = []

    if len(date_string) != 6:
        errors.append(
            f"Invalid {field_name} date length."
        )
        return errors

    if not date_string.isdigit():
        errors.append(
            f"Invalid {field_name} date field."
        )
        return errors

    try:

        year = int(date_string[0:2])
        month = int(date_string[2:4])
        day = int(date_string[4:6])

        # MRZ uses a two-digit year.
        # Use 2000-2049 / 1950-1999 convention
        # for this prototype.

        if year <= 49:
            full_year = 2000 + year
        else:
            full_year = 1900 + year

        datetime(
            full_year,
            month,
            day
        )

    except ValueError:

        errors.append(
            f"Invalid {field_name} date."
        )

    return errors


# ==================================================
# CHECK DIGIT
# ==================================================

def calculate_check_digit(data):
    """
    ICAO MRZ check digit calculation.

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

            value = ord(char) - ord("A") + 10

        else:

            value = 0

        total += (
            value *
            weights[index % 3]
        )

    return total % 10


# ==================================================
# CHECK DIGIT VALIDATION
# ==================================================

def validate_check_digit(
    data,
    check_digit,
    field_name
):

    errors = []

    if not check_digit.isdigit():

        errors.append(
            f"Invalid {field_name} check digit."
        )

        return errors

    expected = calculate_check_digit(data)

    actual = int(check_digit)

    if expected != actual:

        errors.append(
            f"Invalid {field_name} check digit."
        )

    return errors


# ==================================================
# MRZ STRUCTURE VALIDATION
# ==================================================

def validate_mrz_structure(
    line1,
    line2
):

    errors = []

    # --------------------------------------------------
    # CLEAN INPUT
    # --------------------------------------------------

    line1 = line1.upper().strip()
    line2 = line2.upper().strip()

    # --------------------------------------------------
    # LENGTH
    # --------------------------------------------------

    if len(line1) != 44:

        errors.append(
            "Line 1 must contain exactly 44 characters."
        )

    if len(line2) != 44:

        errors.append(
            "Line 2 must contain exactly 44 characters."
        )

    # --------------------------------------------------
    # CHARACTER VALIDATION
    # --------------------------------------------------

    if len(line1) == 44:

        errors.extend(
            validate_characters(
                line1,
                1
            )
        )

    if len(line2) == 44:

        errors.extend(
            validate_characters(
                line2,
                2
            )
        )

    # --------------------------------------------------
    # LINE 1
    # --------------------------------------------------

    if len(line1) == 44:

        # Passport document type

        if line1[0] != "P":

            errors.append(
                "Invalid passport document type."
            )

        # Second character should normally be
        # '<' for ordinary passports.

        if line1[1] != "<":

            errors.append(
                "Invalid passport document format."
            )

        # Issuing country

        country = line1[2:5]

        if not country.isalpha():

            errors.append(
                "Invalid issuing country."
            )

        # Country code must be exactly 3 letters

        if len(country) != 3:

            errors.append(
                "Issuing country must contain 3 letters."
            )

    # --------------------------------------------------
    # LINE 2
    # --------------------------------------------------

    if len(line2) == 44:

        # ----------------------------------------------
        # PASSPORT NUMBER
        # ----------------------------------------------

        passport_number = line2[0:9]

        passport_check_digit = line2[9]

        # Passport number should contain only
        # letters, numbers and filler '<'

        if not re.match(
            r"^[A-Z0-9<]{9}$",
            passport_number
        ):

            errors.append(
                "Invalid passport number format."
            )

        # Check digit

        errors.extend(
            validate_check_digit(
                passport_number,
                passport_check_digit,
                "passport number"
            )
        )

        # ----------------------------------------------
        # NATIONALITY
        # ----------------------------------------------

        nationality = line2[10:13]

        if not nationality.isalpha():

            errors.append(
                "Invalid nationality."
            )

        if len(nationality) != 3:

            errors.append(
                "Nationality must contain 3 letters."
            )

        # ----------------------------------------------
        # DATE OF BIRTH
        # ----------------------------------------------

        dob = line2[13:19]

        errors.extend(
            validate_date(
                dob,
                "date of birth"
            )
        )

        # DOB check digit

        birth_check_digit = line2[19]

        errors.extend(
            validate_check_digit(
                dob,
                birth_check_digit,
                "date of birth"
            )
        )

        # ----------------------------------------------
        # SEX
        # ----------------------------------------------

        sex = line2[20]

        if sex not in ["M", "F", "<"]:

            errors.append(
                "Invalid sex field."
            )

        # ----------------------------------------------
        # EXPIRY DATE
        # ----------------------------------------------

        expiry = line2[21:27]

        errors.extend(
            validate_date(
                expiry,
                "expiry"
            )
        )

        # Expiry check digit

        expiry_check_digit = line2[27]

        errors.extend(
            validate_check_digit(
                expiry,
                expiry_check_digit,
                "expiry date"
            )
        )

        # ----------------------------------------------
        # EXPIRY STATUS
        # ----------------------------------------------

        if expiry.isdigit():

            try:

                yy = int(expiry[0:2])
                mm = int(expiry[2:4])
                dd = int(expiry[4:6])

                if yy <= 49:
                    year = 2000 + yy
                else:
                    year = 1900 + yy

                expiry_date = datetime(
                    year,
                    mm,
                    dd
                )

                today = datetime.today()

                if expiry_date < today:

                    errors.append(
                        "Passport has expired."
                    )

            except ValueError:

                pass

    # ==================================================
    # FINAL RESULT
    # ==================================================

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }