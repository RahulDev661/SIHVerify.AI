import cv2
import pytesseract

from ai_service.ocr.preprocess import preprocess_mrz


pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


image_path = "sample_data/passport_test.png"

# -----------------------------------------
# PREPROCESS MRZ
# -----------------------------------------

processed = preprocess_mrz(
    image_path
)


cv2.imwrite(
    "output/processed_mrz.png",
    processed
)


# -----------------------------------------
# OCR
# -----------------------------------------

config = (
    "--oem 3 "
    "--psm 6 "
    "-c tessedit_char_whitelist="
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<"
)


text = pytesseract.image_to_string(
    processed,
    config=config
)


print()
print("========== MRZ OCR TEST ==========")
print()

print(text)

print()
print("Saved processed image as:")
print("output/processed_mrz.png")

print("===================================")