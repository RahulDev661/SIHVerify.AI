from ai_service.face.recognizer import compare_faces


# ==========================================
# FACE IMAGES
# ==========================================

passport_face = "output/passport_face.png"

same_person = "sample_data/user_face.png"

different_person = "sample_data/different_person.jpeg"


# ==========================================
# HEADER
# ==========================================

print()
print("========================================")
print("       VERIDEX FACE VERIFICATION")
print("========================================")
print()


# ==========================================
# TEST 1 — SAME PERSON
# ==========================================

print("========== TEST 1: SAME PERSON ==========")

print("Passport face:", passport_face)
print("User face:", same_person)

try:

    result = compare_faces(
        passport_face,
        same_person
    )

    print()
    print("Similarity:", result["similarity"])
    print("Threshold:", result["threshold"])
    print("Matched:", result["matched"])

except Exception as e:

    print()
    print("ERROR:", e)


print()


# ==========================================
# TEST 2 — DIFFERENT PERSON
# ==========================================

print("======= TEST 2: DIFFERENT PERSON ========")

print("Passport face:", passport_face)
print("Other face:", different_person)

try:

    result = compare_faces(
        passport_face,
        different_person
    )

    print()
    print("Similarity:", result["similarity"])
    print("Threshold:", result["threshold"])
    print("Matched:", result["matched"])

except Exception as e:

    print()
    print("ERROR:", e)


# ==========================================
# END
# ==========================================

print()
print("========================================")
print("       FACE VERIFICATION COMPLETE")
print("========================================")