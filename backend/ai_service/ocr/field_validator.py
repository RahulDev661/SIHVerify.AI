from datetime import datetime


def normalize_text(value):
    if value is None:
        return ""

    return str(value).strip().upper()


def normalize_passport_number(value):
    """
    Remove spaces and separators from passport number.
    """

    value = normalize_text(value)

    return (
        value
        .replace(" ", "")
        .replace("-", "")
    )


def normalize_gender(value):
    """
    Convert common gender values to MRZ format.
    """

    value = normalize_text(value)

    mapping = {
        "MALE": "M",
        "M": "M",
        "FEMALE": "F",
        "F": "F",
        "UNSPECIFIED": "<",
        "X": "<",
        "<": "<"
    }

    return mapping.get(
        value,
        value
    )


def normalize_date(value):
    """
    Convert common date formats to DD/MM/YYYY.
    """

    value = normalize_text(value)

    if not value:
        return ""

    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d.%m.%Y"
    ]

    for date_format in formats:

        try:
            parsed = datetime.strptime(
                value,
                date_format
            )

            return parsed.strftime(
                "%d/%m/%Y"
            )

        except ValueError:
            continue

    return value


def compare_fields(
    visible_fields: dict,
    mrz_fields: dict
):
    """
    Compare visible passport OCR fields
    against parsed MRZ fields.

    Fields:
        passportNumber
        nationality
        dob
        expiry
        sex
    """

    checks = {}
    mismatches = []

    # ==========================================
    # PASSPORT NUMBER
    # ==========================================

    visible_passport = normalize_passport_number(
        visible_fields.get(
            "passportNumber"
        )
    )

    mrz_passport = normalize_passport_number(
        mrz_fields.get(
            "passportNumber"
        )
    )

    passport_match = (
        visible_passport != ""
        and visible_passport == mrz_passport
    )

    checks[
        "passportNumberMatch"
    ] = passport_match

    if not passport_match:
        mismatches.append(
            "Passport number does not match MRZ"
        )

    # ==========================================
    # NATIONALITY
    # ==========================================

    visible_nationality = normalize_text(
        visible_fields.get(
            "nationality"
        )
    )

    mrz_nationality = normalize_text(
        mrz_fields.get(
            "nationality"
        )
    )

    nationality_match = (
        visible_nationality != ""
        and visible_nationality
        == mrz_nationality
    )

    checks[
        "nationalityMatch"
    ] = nationality_match

    if not nationality_match:
        mismatches.append(
            "Nationality does not match MRZ"
        )

    # ==========================================
    # DATE OF BIRTH
    # ==========================================

    visible_dob = normalize_date(
        visible_fields.get(
            "dob"
        )
    )

    mrz_dob = normalize_date(
        mrz_fields.get(
            "dob"
        )
    )

    dob_match = (
        visible_dob != ""
        and visible_dob == mrz_dob
    )

    checks[
        "dobMatch"
    ] = dob_match

    if not dob_match:
        mismatches.append(
            "Date of birth does not match MRZ"
        )

    # ==========================================
    # EXPIRY DATE
    # ==========================================

    visible_expiry = normalize_date(
        visible_fields.get(
            "expiry"
        )
    )

    mrz_expiry = normalize_date(
        mrz_fields.get(
            "expiry"
        )
    )

    expiry_match = (
        visible_expiry != ""
        and visible_expiry
        == mrz_expiry
    )

    checks[
        "expiryMatch"
    ] = expiry_match

    if not expiry_match:
        mismatches.append(
            "Expiry date does not match MRZ"
        )

    # ==========================================
    # GENDER / SEX
    # ==========================================

    visible_sex = normalize_gender(
        visible_fields.get(
            "sex"
        )
    )

    mrz_sex = normalize_gender(
        mrz_fields.get(
            "sex"
        )
    )

    sex_match = (
        visible_sex != ""
        and visible_sex == mrz_sex
    )

    checks[
        "sexMatch"
    ] = sex_match

    if not sex_match:
        mismatches.append(
            "Sex does not match MRZ"
        )

    # ==========================================
    # CONSISTENCY SCORE
    # ==========================================

    total_checks = len(
        checks
    )

    passed_checks = sum(
        1
        for value in checks.values()
        if value
    )

    consistency_score = (
        (
            passed_checks
            / total_checks
        )
        * 100
        if total_checks > 0
        else 0
    )

    # ==========================================
    # STATUS
    # ==========================================

    if consistency_score == 100:

        status = "CONSISTENT"

    elif consistency_score >= 60:

        status = "REVIEW_REQUIRED"

    else:

        status = "INCONSISTENT"

    # ==========================================
    # RESULT
    # ==========================================

    return {

        "checks": checks,

        "consistencyScore": round(
            consistency_score,
            2
        ),

        "status": status,

        "mismatches": mismatches,

        "normalizedValues": {

            "visible": {
                "passportNumber":
                    visible_passport,
                "nationality":
                    visible_nationality,
                "dob":
                    visible_dob,
                "expiry":
                    visible_expiry,
                "sex":
                    visible_sex
            },

            "mrz": {
                "passportNumber":
                    mrz_passport,
                "nationality":
                    mrz_nationality,
                "dob":
                    mrz_dob,
                "expiry":
                    mrz_expiry,
                "sex":
                    mrz_sex
            }
        }
    }