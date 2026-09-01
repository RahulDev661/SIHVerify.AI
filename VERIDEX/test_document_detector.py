from ai_service.ocr.extractor import process_passport


print()
print("========================================")
print("        VERIDEX DOCUMENT SCREENING")
print("========================================")
print()

print("Select Document Type:")
print()
print("1. Passport")
print("2. Visa")
print("3. ID Card")
print("4. Driving Licence")
print()

choice = input("Enter choice (1-4): ")

document_types = {
    "1": "passport",
    "2": "visa",
    "3": "id_card",
    "4": "driving_licence"
}

if choice not in document_types:
    print()
    print("Invalid document type.")
    exit()

document_type = document_types[choice]

print()
print("Selected Document:", document_type)


# ==========================================
# PASSPORT
# ==========================================

if document_type == "passport":

    image_path = "test_mrz_document.png"

    print()
    print("Routing to Passport OCR + MRZ pipeline...")
    print()
    
    try:

        result = process_passport(
            image_path
        )

        print()
        print("========== PASSPORT RESULT ==========")
        print()

        print(result)

        print()
        print("=====================================")

    except Exception as e:

        print()
        print("PASSPORT PIPELINE ERROR:")
        print(e)


# ==========================================
# OTHER DOCUMENTS
# ==========================================

elif document_type == "visa":

    print()
    print("Visa OCR pipeline not implemented yet.")


elif document_type == "id_card":

    print()
    print("ID Card OCR pipeline not implemented yet.")


elif document_type == "driving_licence":

    print()
    print("Driving Licence OCR pipeline not implemented yet.")


print()
print("========================================")