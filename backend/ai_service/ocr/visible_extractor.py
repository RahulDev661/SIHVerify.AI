import cv2
import pytesseract
import os
import re
from datetime import datetime

from ai_service.config import TESSERACT_CMD


# ==================================================
# TESSERACT PATH
# ==================================================
# Resolved in ai_service.config: env var override -> PATH lookup ->
# Windows default fallback. No more hardcoded Windows-only path.

if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


# ==================================================
# OCR SINGLE FIELD REGION
# ==================================================

def _ocr_region(
    image,
    x1_ratio,
    y1_ratio,
    x2_ratio,
    y2_ratio,
    whitelist=None,
    scale=4.0,
    psm=7
):
    """
    Crop and OCR one specific passport field.

    Coordinates are stored as ratios so the same
    passport layout can work at different resolutions.
    """

    height, width = image.shape[:2]

    x1 = int(width * x1_ratio)
    y1 = int(height * y1_ratio)

    x2 = int(width * x2_ratio)
    y2 = int(height * y2_ratio)

    region = image[
        y1:y2,
        x1:x2
    ]

    if region.size == 0:
        return ""

    # ==================================================
    # GRAYSCALE
    # ==================================================

    gray = cv2.cvtColor(
        region,
        cv2.COLOR_BGR2GRAY
    )

    # ==================================================
    # UPSCALE
    # ==================================================

    gray = cv2.resize(
        gray,
        None,
        fx=scale,
        fy=scale,
        interpolation=cv2.INTER_CUBIC
    )

    # ==================================================
    # OCR CONFIGURATION
    # ==================================================

    config = (
    "--oem 3 "
    f"--psm {psm}"
)

    if whitelist:

        config += (
            " -c tessedit_char_whitelist="
            + whitelist
        )

    # ==================================================
    # OCR
    # ==================================================

    text = pytesseract.image_to_string(
        gray,
        config=config
    )

    return text.strip()


# ==================================================
# CLEAN PASSPORT NUMBER
# ==================================================

def _clean_passport_number(text):

    text = text.upper()

    text = re.sub(
        r"[^A-Z0-9]",
        "",
        text
    )

    matches = re.findall(
        r"[A-Z][A-Z0-9]{7,9}",
        text
    )

    if matches:
        return matches[0]

    return text


# ==================================================
# CLEAN NATIONALITY
# ==================================================

def _clean_nationality(text):

    text = text.upper()

    text = re.sub(
        r"[^A-Z]",
        "",
        text
    )

    if len(text) >= 3:
        return text[:3]

    return text


# ==================================================
# CLEAN SEX
# ==================================================

def _clean_sex(text):

    text = text.upper()

    text = text.replace(
        " ",
        ""
    )

    # Turkish passport:
    # E/M = Erkek / Male

    if "E/M" in text:
        return "M"

    # Turkish passport:
    # K/F = Kadin / Female

    if "K/F" in text:
        return "F"

    if "M" in text:
        return "M"

    if "F" in text:
        return "F"

    return ""


# ==================================================
# PARSE DATE
# ==================================================

def _parse_visible_date(text):
    """
    Convert visible passport dates like:

        14 AGU / AUG 1984
        15 EYL / SEP 2032

    into:

        14/08/1984
        15/09/2032
    """

    if not text:
        return ""

    text = text.upper()

    text = text.replace(
        "|",
        "/"
    )

    text = text.replace(
        "\\",
        "/"
    )

    month_map = {

        "JAN": 1,
        "FEB": 2,
        "MAR": 3,
        "APR": 4,
        "MAY": 5,
        "JUN": 6,
        "JUL": 7,
        "AUG": 8,
        "SEP": 9,
        "OCT": 10,
        "NOV": 11,
        "DEC": 12
    }

    # ==================================================
    # TEXT MONTH FORMAT
    # ==================================================

    for month_text, month_number in month_map.items():

        pattern = (
            r"(\d{1,2})"
            r".{0,20}"
            + month_text +
            r".{0,10}"
            r"(\d{4})"
        )

        match = re.search(
            pattern,
            text
        )

        if match:

            day = int(
                match.group(1)
            )

            year = int(
                match.group(2)
            )

            try:

                date_value = datetime(
                    year,
                    month_number,
                    day
                )

                return date_value.strftime(
                    "%d/%m/%Y"
                )

            except ValueError:
                pass

    # ==================================================
    # NUMERIC FALLBACK
    # ==================================================

    match = re.search(
        r"(\d{1,2})"
        r"[\/\-. ]"
        r"(\d{1,2})"
        r"[\/\-. ]"
        r"(\d{4})",
        text
    )

    if match:

        day = int(
            match.group(1)
        )

        month = int(
            match.group(2)
        )

        year = int(
            match.group(3)
        )

        try:

            date_value = datetime(
                year,
                month,
                day
            )

            return date_value.strftime(
                "%d/%m/%Y"
            )

        except ValueError:
            pass

    return ""


# ==================================================
# EXTRACT VISIBLE PASSPORT FIELDS
# ==================================================

def extract_visible_fields(
    image_path: str
):
    """
    Extract visible fields from the current
    Turkish passport test layout.

    Extracted fields:
        passportNumber
        nationality
        dob
        expiry
        sex
    """

    # ==================================================
    # CHECK FILE
    # ==================================================

    if not os.path.exists(
        image_path
    ):

        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    # ==================================================
    # LOAD IMAGE
    # ==================================================

    image = cv2.imread(
        image_path
    )

    if image is None:

        raise ValueError(
            f"Could not read image: {image_path}"
        )

    # ==================================================
    # PASSPORT NUMBER
    #
    # Approx on 1280x866:
    # x = 650 -> 825
    # y = 95  -> 145
    # ==================================================

    passport_raw = _ocr_region(

        image,

        0.508,
        0.110,
        0.645,
        0.168,

        whitelist=(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789"
        ),

        scale=4.0
    )

    passport_number = (
        _clean_passport_number(
            passport_raw
        )
    )

    # ==================================================
    # DATE OF BIRTH
    #
    # Approx:
    # x = 385 -> 630
    # y = 285 -> 330
    # ==================================================

    dob_raw = _ocr_region(

     image,

     0.300,
     0.329,
     0.495,
     0.382,

     whitelist=(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789/"
     ),

     scale=4.0,

     psm=6
)

    dob = _parse_visible_date(
     dob_raw
)

    # ==================================================
    # NATIONALITY
    #
    # Approx:
    # x = 390 -> 455
    # y = 340 -> 380
    # ==================================================

    nationality_raw = _ocr_region(

        image,

        0.305,
        0.392,
        0.355,
        0.438,

        whitelist=(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        ),

        scale=5.0
    )

    nationality = (
        _clean_nationality(
            nationality_raw
        )
    )

    # ==================================================
    # SEX
    #
    # Approx:
    # x = 385 -> 455
    # y = 398 -> 430
    # ==================================================

    sex_raw = _ocr_region(

        image,

        0.300,
        0.460,
        0.356,
        0.497,

        whitelist=(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ/"
        ),

        scale=6.0
    )

    sex = _clean_sex(
        sex_raw
    )

    # ==================================================
    # EXPIRY
    #
    # Approx:
    # x = 385 -> 625
    # y = 505 -> 550
    # ==================================================

    expiry_raw = _ocr_region(

        image,

        0.301,
        0.584,
        0.488,
        0.636,

        scale=4.0
    )

    expiry = _parse_visible_date(
        expiry_raw
    )

    # ==================================================
    # DEBUG OUTPUT
    # ==================================================

    print()
    print(
        "========================================"
    )

    print(
        "       VISIBLE FIELD EXTRACTION"
    )

    print(
        "========================================"
    )

    print()

    print(
        "Passport raw:",
        repr(passport_raw)
    )

    print(
        "Passport Number:",
        passport_number
    )

    print()

    print(
        "DOB raw:",
        repr(dob_raw)
    )

    print(
        "DOB:",
        dob
    )

    print()

    print(
        "Nationality raw:",
        repr(nationality_raw)
    )

    print(
        "Nationality:",
        nationality
    )

    print()

    print(
        "Sex raw:",
        repr(sex_raw)
    )

    print(
        "Sex:",
        sex
    )

    print()

    print(
        "Expiry raw:",
        repr(expiry_raw)
    )

    print(
        "Expiry:",
        expiry
    )

    print()

    print(
        "========================================"
    )

    # ==================================================
    # RETURN
    # ==================================================

    return {

        "passportNumber":
            passport_number,

        "nationality":
            nationality,

        "dob":
            dob,

        "expiry":
            expiry,

        "sex":
            sex,

        "raw": {

            "passportNumber":
                passport_raw,

            "nationality":
                nationality_raw,

            "dob":
                dob_raw,

            "expiry":
                expiry_raw,

            "sex":
                sex_raw
        }
    }