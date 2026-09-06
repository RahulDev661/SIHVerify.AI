"""
Ad hoc smoke test for the visible-field <-> MRZ consistency check.

Not a pytest-assertion suite (see note in README) — run directly:
    cd tests && python test_field_validator.py
"""

from ai_service.ocr.field_validator import compare_fields

visible_fields = {
    "passportNumber": "U 12345678",
    "nationality": "tur",
    "dob": "14-08-1984",
    "expiry": "2032-09-15",
    "sex": "Male",
}

mrz_fields = {
    "passportNumber": "U12345678",
    "nationality": "TUR",
    "dob": "14/08/1984",
    "expiry": "15/09/2032",
    "sex": "M",
}

result = compare_fields(visible_fields, mrz_fields)

print()
print("========================================")
print("     VERIDEX FIELD CONSISTENCY TEST")
print("========================================")
print("Checks:", result["checks"])
print("Consistency Score:", result["consistencyScore"])
print("Status:", result["status"])
print("Mismatches:", result["mismatches"] or "None")
