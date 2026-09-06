from ai_service.ocr.mrz_normalizer import (
    normalize_mrz_lines
)


line1 = "P<INDRAHUL<K<DEV<BERA<K<<<<<<<<<<"

line2 = "P1234567<1IND0405122M3005121<<<<<<<<<<<<<<<<"

normalized_line1, normalized_line2 = (
    normalize_mrz_lines(
        line1,
        line2
    )
)


print()
print("========== NORMALIZER TEST ==========")
print()

print("Original Line 1:")
print(line1)

print()
print("Normalized Line 1:")
print(normalized_line1)

print()

print("Original Line 2:")
print(line2)

print()
print("Normalized Line 2:")
print(normalized_line2)

print()
print("======================================")