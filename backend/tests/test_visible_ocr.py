"""
Ad hoc smoke test for Module 1b — visible (non-MRZ) field OCR.

Not a pytest-assertion suite (see note in README) — run directly:
    cd tests && python test_visible_ocr.py
"""

from ai_service.ocr.visible_extractor import extract_visible_fields

result = extract_visible_fields("sample_data/passport_test.png")

print()
print("FINAL VISIBLE FIELDS:")
print(result)
