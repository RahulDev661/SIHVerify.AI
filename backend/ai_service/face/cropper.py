import cv2


def crop_passport_face(
    image_path: str,
    faces: list,
    output_path: str = "passport_face.png"
):
    """
    Select the most likely passport portrait,
    add generous padding, and create a larger
    face crop for face recognition.
    """

    image = cv2.imread(image_path)

    if image is None:
        raise FileNotFoundError(
            f"Could not open image: {image_path}"
        )

    if not faces:
        raise ValueError(
            "No faces available for cropping."
        )

    height, width = image.shape[:2]

    # ==========================================
    # SELECT PASSPORT PORTRAIT
    # ==========================================

    # Passport portrait is normally on the
    # left side of the document.

    left_candidates = [
        face for face in faces
        if face["x"] < width * 0.55
    ]

    if left_candidates:

        selected_face = max(
            left_candidates,
            key=lambda f: f["width"] * f["height"]
        )

    else:

        selected_face = max(
            faces,
            key=lambda f: f["width"] * f["height"]
        )

    x = selected_face["x"]
    y = selected_face["y"]
    w = selected_face["width"]
    h = selected_face["height"]

    print()
    print("Selected passport face:")
    print(selected_face)

    # ==========================================
    # GENEROUS PADDING
    # ==========================================

    # More padding gives the recognizer some
    # surrounding facial information.

    padding_x = int(w * 1.2)
    padding_y = int(h * 1.2)

    x1 = max(0, x - padding_x)
    y1 = max(0, y - padding_y)

    x2 = min(
        width,
        x + w + padding_x
    )

    y2 = min(
        height,
        y + h + padding_y
    )

    face_crop = image[
        y1:y2,
        x1:x2
    ]

    if face_crop.size == 0:
        raise ValueError(
            "Face crop is empty."
        )

    # ==========================================
    # UPSCALE
    # ==========================================

    crop_height, crop_width = face_crop.shape[:2]

    target_size = 400

    scale = max(
        target_size / crop_width,
        target_size / crop_height
    )

    if scale > 1:

        new_width = int(
            crop_width * scale
        )

        new_height = int(
            crop_height * scale
        )

        face_crop = cv2.resize(
            face_crop,
            (new_width, new_height),
            interpolation=cv2.INTER_CUBIC
        )

    # ==========================================
    # SAVE
    # ==========================================

    success = cv2.imwrite(
        output_path,
        face_crop
    )

    if not success:
        raise IOError(
            f"Could not save face crop: {output_path}"
        )

    print()
    print("Face crop saved:")
    print(output_path)

    print(
        "Final crop size:",
        face_crop.shape[1],
        "x",
        face_crop.shape[0]
    )

    return {
        "selectedFace": selected_face,

        "crop": {
            "x": x1,
            "y": y1,
            "width": x2 - x1,
            "height": y2 - y1
        },

        "output": output_path
    }