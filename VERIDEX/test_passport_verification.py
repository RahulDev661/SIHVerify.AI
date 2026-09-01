from ai_service.ocr.extractor import process_passport
from ai_service.face.detector import detect_faces
from ai_service.face.cropper import crop_passport_face
from ai_service.face.recognizer import compare_faces


# ==========================================
# FILES
# ==========================================

passport_image = "passport_test.png"
user_face_image = "user_face.png"

passport_face_image = "passport_face.png"


# ==========================================
# HEADER
# ==========================================

print()
print("========================================")
print("       VERIDEX PASSPORT VERIFICATION")
print("========================================")
print()


try:

    # ======================================
    # STEP 1 — PASSPORT MRZ
    # ======================================

    print("[1] PASSPORT OCR + MRZ")
    print("----------------------------------------")

    passport_result = process_passport(
        passport_image
    )

    structure = passport_result.get(
        "structureValidation",
        {}
    )

    mrz_valid = structure.get(
        "valid",
        False
    )

    print()
    print("Passport Number:",
          passport_result.get("passportNumber"))

    print("Name:",
          passport_result.get("surname"),
          passport_result.get("givenNames"))

    print("Nationality:",
          passport_result.get("nationality"))

    print("Date of Birth:",
          passport_result.get("dob"))

    print("Expiry:",
          passport_result.get("expiry"))

    print()
    print("MRZ Structure Valid:",
          mrz_valid)


    # ======================================
    # STEP 2 — FACE DETECTION
    # ======================================

    print()
    print("[2] PASSPORT FACE DETECTION")
    print("----------------------------------------")

    faces = detect_faces(
        passport_image
    )

    print()
    print("Faces detected:",
          len(faces))

    if not faces:

        raise ValueError(
            "No face detected in passport."
        )


    # ======================================
    # STEP 3 — PASSPORT FACE CROP
    # ======================================

    print()
    print("[3] PASSPORT FACE EXTRACTION")
    print("----------------------------------------")

    crop_result = crop_passport_face(
        passport_image,
        faces,
        passport_face_image
    )

    print()
    print(
        "Passport face saved as:",
        crop_result["output"]
    )


    # ======================================
    # STEP 4 — FACE VERIFICATION
    # ======================================

    print()
    print("[4] FACE VERIFICATION")
    print("----------------------------------------")

    face_result = compare_faces(
        passport_face_image,
        user_face_image
    )

    similarity = face_result[
        "similarity"
    ]

    threshold = face_result[
        "threshold"
    ]

    face_match = face_result[
        "matched"
    ]

    print()
    print("Similarity:",
          similarity)

    print("Threshold:",
          threshold)

    print("Face Match:",
          face_match)


    # ======================================
    # STEP 5 — FINAL DECISION
    # ======================================

    print()
    print("========================================")
    print("       FINAL VERIFICATION")
    print("========================================")

    print()

    print(
        "MRZ VALID       :",
        "PASS" if mrz_valid else "FAIL"
    )

    print(
        "FACE MATCH      :",
        "PASS" if face_match else "FAIL"
    )

    # --------------------------------------
    # FINAL RESULT
    # --------------------------------------

    final_verified = (
        mrz_valid
        and face_match
    )

    print()

    if final_verified:

        print(
            "FINAL RESULT    : VERIFIED"
        )

    else:

        print(
            "FINAL RESULT    : REJECTED"
        )

    print()
    print("========================================")


except Exception as e:

    print()
    print("========================================")
    print("       VERIDEX PIPELINE ERROR")
    print("========================================")
    print()
    print(e)
    print()