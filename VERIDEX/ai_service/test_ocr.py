import cv2
import pytesseract

from ai_service.ocr.preprocess import preprocess_image


# Tesseract installation path
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


# Input document
image_path = "test_document.png"


# -----------------------------------
# STEP 1: PREPROCESS IMAGE
# -----------------------------------

processed_image = preprocess_image(image_path)


# -----------------------------------
# STEP 2: SAVE PROCESSED IMAGE
# -----------------------------------

cv2.imwrite(
    "processed_document.png",
    processed_image
)


# -----------------------------------
# STEP 3: OCR
# -----------------------------------

text = pytesseract.image_to_string(
    processed_image,
    config="--psm 6"
)


# -----------------------------------
# STEP 4: DISPLAY RESULT
# -----------------------------------

print()
print("========== OCR RESULT ==========")
print()

print(text)

print()
print("================================")