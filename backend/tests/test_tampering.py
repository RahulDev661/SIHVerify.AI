"""
Ad hoc smoke test for Module 3 — tampering / forensics screening.

Not a pytest-assertion suite (see note in README) — run directly:
    cd tests && python test_tampering.py
"""

from ai_service.tampering.detector import detect_tampering

IMAGES = [
    "sample_data/passport_test.png",
    "sample_data/passport_photo_tampered.png",
    "sample_data/passport_stamp_tampered.png",
    "sample_data/passport_text_tampered.png",
    "sample_data/passport_dob_tampered.png",
]

print()
print("========================================")
print("       VERIDEX TAMPERING DETECTION")
print("========================================")

for image_path in IMAGES:
    print()
    print(f"--- {image_path} ---")

    try:
        result = detect_tampering(image_path)

        print("Tampering Score:", result["tamperingScore"])
        print("Status:", result["status"])

        if result["reasons"]:
            print("Reasons:")
            for reason in result["reasons"]:
                print(" -", reason)
        else:
            print("No suspicious indicators detected.")

    except Exception as exc:
        print("ERROR:", exc)

print()
print("========================================")
