import json

from ai_service.ocr.mrz_parser import (
    parse_passport_mrz,
    calculate_check_digit
)


# -----------------------------------------
# PASSPORT DATA
# -----------------------------------------

passport_number = "P1234567<"
nationality = "IND"

dob = "040512"
sex = "M"

expiry = "300512"


# -----------------------------------------
# CALCULATE REAL CHECK DIGITS
# -----------------------------------------

passport_check = str(
    calculate_check_digit(passport_number)
)

dob_check = str(
    calculate_check_digit(dob)
)

expiry_check = str(
    calculate_check_digit(expiry)
)


# -----------------------------------------
# LINE 1
# -----------------------------------------

line1 = "P<INDRAHUL<DEV<BERA"
line1 = line1.ljust(44, "<")


# -----------------------------------------
# LINE 2
# -----------------------------------------

line2 = (
    passport_number
    + passport_check
    + nationality
    + dob
    + dob_check
    + sex
    + expiry
    + expiry_check
)

line2 = line2.ljust(44, "<")


# -----------------------------------------
# DISPLAY MRZ
# -----------------------------------------

print("Line 1:")
print(line1)

print()
print("Line 1 length:", len(line1))

print()

print("Line 2:")
print(line2)

print()
print("Line 2 length:", len(line2))

print()

print("Passport check digit:", passport_check)
print("DOB check digit:", dob_check)
print("Expiry check digit:", expiry_check)


# -----------------------------------------
# PARSE
# -----------------------------------------

result = parse_passport_mrz(
    line1,
    line2
)


# -----------------------------------------
# DISPLAY RESULT
# -----------------------------------------

print()
print("========== MRZ PARSER RESULT ==========")
print()

print(
    json.dumps(
        result,
        indent=4
    )
)

print()
print("========================================")