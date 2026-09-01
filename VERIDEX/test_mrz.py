from ai_service.ocr.mrz_parser import find_mrz_lines


sample_text = """
VERIDEX DOCUMENT SCREENING

Name: RAHUL DEV BERA
Passport Number: P1234567
Date of Birth: 12/05/2004
Nationality: IND
Expiry: 12/05/2030

P<INDRAHUL<DEV<BERA<<<<<<<<<<<<<<<<<<<<
P1234567<8IND0405129M3005127<<<<<<<<<<
"""


mrz_lines = find_mrz_lines(sample_text)


print()
print("========== MRZ DETECTION ==========")
print()

for line in mrz_lines:
    print(line)

print()
print("====================================")
