from ai_service.ocr.mrz_candidate import (
    correct_mrz_line2
)


ocr_line = (
    "P1I12345607<L1N004051122M3005121<<<<<<KKKKKK"
)


result = correct_mrz_line2(
    ocr_line
)


print()
print("==========================================")
print("        MRZ CORRECTION ANALYSIS")
print("==========================================")

print()

print("Original OCR:")
print(result["original"])

print()

print("Normalized:")
print(result["normalized"])

print()

print("Confidence:")
print(result["confidence"])

print()

print("Verified:")
print(result["verified"])

print()

print("Structure valid:")
print(
    result["analysis"]["structureValid"]
)

print()

print("Errors:")

for error in result["analysis"]["errors"]:

    print(
        " -",
        error
    )

print()

print("Check digits:")

for key, value in result[
    "analysis"
]["checkDigits"].items():

    print(
        f" - {key}: {value}"
    )

print()

print("==========================================")