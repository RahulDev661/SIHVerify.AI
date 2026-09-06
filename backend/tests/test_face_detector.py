from ai_service.face.detector import detect_faces
from ai_service.face.cropper import crop_passport_face


# ==========================================
# TEST IMAGE
# ==========================================

image_path = "sample_data/passport_test.png"
output_path = "output/passport_face.png"


print()
print("========================================")
print("       VERIDEX FACE PROCESSING")
print("========================================")
print()

print("Image:", image_path)

try:

    # --------------------------------------
    # STEP 1: DETECT FACES
    # --------------------------------------

    faces = detect_faces(image_path)

    print()
    print("Faces detected:", len(faces))
    print()

    for index, face in enumerate(
        faces,
        start=1
    ):

        print(f"Face {index}:")
        print("X:", face["x"])
        print("Y:", face["y"])
        print("Width:", face["width"])
        print("Height:", face["height"])
        print(
            "Confidence:",
            face["confidence"]
        )
        print()

    # --------------------------------------
    # STEP 2: SELECT + CROP
    # --------------------------------------

    if not faces:

        raise ValueError(
            "No face detected in passport."
        )

    result = crop_passport_face(
        image_path,
        faces,
        output_path
    )

    print()
    print("========== SELECTED FACE ==========")

    print(
        "Selected face:",
        result["selectedFace"]
    )

    print()
    print("Crop:")
    print("X:", result["crop"]["x"])
    print("Y:", result["crop"]["y"])
    print("Width:", result["crop"]["width"])
    print("Height:", result["crop"]["height"])

    print()
    print("Saved face image as:")
    print(result["output"])

except Exception as e:

    print()
    print("FACE PROCESSING ERROR:")
    print(e)

print()
print("========================================")