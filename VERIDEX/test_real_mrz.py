import json
import pytesseract

from ai_service.ocr.preprocess import preprocess_image
from ai_service.ocr.mrz_parser import parse_mrz_from_ocr


# -----------------------------------------
# TESSERACT PATH
# -----------------------------------------

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


# -----------------------------------------
# IMAGE
# -----------------------------------------

image_path = "test_mrz_document.png"


# -----------------------------------------
# PREPROCESS
# -----------------------------------------

processed_image = preprocess_image(
    image_path
)


# -----------------------------------------
# OCR
# -----------------------------------------

ocr_text = pytesseract.image_to_string(
    processed_image,
    config="--psm 6"
)


print()
print("========== RAW OCR TEXT ==========")
print()

print(ocr_text)

print()
print("===================================")


# -----------------------------------------
# MRZ
# -----------------------------------------

try:

    result = parse_mrz_from_ocr(
        ocr_text
    )

    print()
    print("========== AUTOMATIC MRZ ==========")
    print()

    print(
        json.dumps(
            result,
            indent=4
        )
    )

    print()
    print("===================================")

except ValueError as error:

    print()
    print("MRZ detection failed:")
    print(error)