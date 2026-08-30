import re
import pytesseract

from ai_service.ocr.preprocess import preprocess_image


# Tesseract installation path
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def extract_text(image_path: str) -> str:
    """
    Preprocess the document image and extract text using OCR.
    """

    processed_image = preprocess_image(image_path)

    text = pytesseract.image_to_string(
        processed_image,
        config="--psm 6"
    )

    return text


def clean_text(text: str) -> str:
    """
    Remove unnecessary spaces and empty lines.
    """

    lines = []

    for line in text.splitlines():

        line = line.strip()

        if line:
            lines.append(line)

    return "\n".join(lines)


def extract_passport_fields(text: str) -> dict:
    """
    Extract basic passport fields from OCR text.
    """

    text = clean_text(text)

    result = {
        "name": None,
        "passportNumber": None,
        "dob": None,
        "nationality": None,
        "expiry": None
    }

    # NAME
    name_match = re.search(
        r"Name\s*:\s*(.+)",
        text,
        re.IGNORECASE
    )

    if name_match:
        result["name"] = name_match.group(1).strip()

    # PASSPORT NUMBER
    passport_match = re.search(
        r"Passport\s*(?:Number|No\.?)?\s*:\s*([A-Z0-9]+)",
        text,
        re.IGNORECASE
    )

    if passport_match:
        result["passportNumber"] = (
            passport_match.group(1).upper()
        )

    # DATE OF BIRTH
    dob_match = re.search(
        r"Date\s*of\s*Birth\s*:\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})",
        text,
        re.IGNORECASE
    )

    if dob_match:
        result["dob"] = dob_match.group(1)

    # NATIONALITY
    nationality_match = re.search(
        r"Nationality\s*:\s*([A-Za-z]+)",
        text,
        re.IGNORECASE
    )

    if nationality_match:
        result["nationality"] = (
            nationality_match.group(1).upper()
        )

    # EXPIRY
    expiry_match = re.search(
        r"Expiry\s*:\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})",
        text,
        re.IGNORECASE
    )

    if expiry_match:
        result["expiry"] = expiry_match.group(1)

    return result


def process_passport(image_path: str) -> dict:
    """
    Complete passport OCR pipeline.

    Image
        ↓
    Preprocessing
        ↓
    OCR
        ↓
    Field extraction
        ↓
    Structured JSON
    """

    raw_text = extract_text(image_path)

    fields = extract_passport_fields(raw_text)

    return {
        "documentType": "passport",
        "fields": fields
    }