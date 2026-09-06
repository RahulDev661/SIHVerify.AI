from ai_service.ocr.mrz_corrector import (
    correct_mrz_line2
)


ocr_line2 = (
    "P1I12345607<L1N004051122M3005121<<<<<<KKKKKK"
)

print()
print("========== MRZ CORRECTION TEST ==========")

print()
print("OCR LINE:")
print(ocr_line2)

corrected = correct_mrz_line2(
    ocr_line2
)

print()
print("CORRECTED LINE:")
print(corrected)

print()
print("Length:", len(corrected))

print("==========================================")