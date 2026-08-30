import json

from ai_service.ocr.extractor import process_passport


image_path = "test_document.png"


result = process_passport(image_path)


print()
print("========== STRUCTURED OCR RESULT ==========")
print()

print(
    json.dumps(
        result,
        indent=4
    )
)

print()
print("============================================")