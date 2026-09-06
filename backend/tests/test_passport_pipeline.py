import json

from ai_service.ocr.extractor import process_passport



image_path = "sample_data/passport_test.png"

print()
print("========================================")
print("       VERIDEX PASSPORT PIPELINE")
print("========================================")
print()


try:

    result = process_passport(
        image_path
    )

    print(
        json.dumps(
            result,
            indent=4
        )
    )

except Exception as e:

    print()
    print("PIPELINE ERROR:")
    print(e)

print()
print("========================================")
