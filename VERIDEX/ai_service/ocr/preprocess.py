import cv2


def preprocess_mrz(image_path: str):

    image = cv2.imread(image_path)

    if image is None:
        raise FileNotFoundError(
            f"Could not open image: {image_path}"
        )

    height, width = image.shape[:2]

    print("Original image:")
    print("Width:", width)
    print("Height:", height)

    # ==========================================
    # MRZ CROP
    # ==========================================
    #
    # MRZ is normally located at the very bottom
    # of the passport data page.
    #
    # Use the bottom 22% instead of 30%.
    #

    crop_start = int(height * 0.70)

    mrz_region = image[
        crop_start:height,
        0:width
    ]

    print(
        "MRZ crop starts at:",
        crop_start
    )

    # ==========================================
    # GRAYSCALE
    # ==========================================

    gray = cv2.cvtColor(
        mrz_region,
        cv2.COLOR_BGR2GRAY
    )

    # ==========================================
    # UPSCALE
    # ==========================================

    gray = cv2.resize(
        gray,
        None,
        fx=4,
        fy=4,
        interpolation=cv2.INTER_CUBIC
    )

    # ==========================================
    # CONTRAST ENHANCEMENT
    # ==========================================

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    gray = clahe.apply(gray)

    # ==========================================
    # LIGHT NOISE REDUCTION
    # ==========================================

    gray = cv2.GaussianBlur(
        gray,
        (3, 3),
        0
    )

    # ==========================================
    # OTSU THRESHOLD
    # ==========================================

    threshold = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    # ==========================================
    # MORPHOLOGICAL CLEANUP
    # ==========================================

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (2, 2)
    )

    threshold = cv2.morphologyEx(
        threshold,
        cv2.MORPH_CLOSE,
        kernel
    )

    return threshold