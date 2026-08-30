import cv2


def preprocess_image(image_path: str):
    """
    Preprocess a document image before OCR.

    Pipeline:
    Image
        ↓
    Resize
        ↓
    Grayscale
        ↓
    Noise Removal
        ↓
    Thresholding
    """

    # Read image
    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(f"Could not read image: {image_path}")

    # -----------------------------------
    # 1. RESIZE
    # -----------------------------------

    height, width = image.shape[:2]

    target_width = 1800

    if width < target_width:

        scale = target_width / width

        image = cv2.resize(
            image,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_CUBIC
        )

    # -----------------------------------
    # 2. GRAYSCALE
    # -----------------------------------

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # -----------------------------------
    # 3. NOISE REMOVAL
    # -----------------------------------

    denoised = cv2.GaussianBlur(
        gray,
        (3, 3),
        0
    )

    # -----------------------------------
    # 4. THRESHOLDING
    # -----------------------------------

    threshold = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11
    )

    return threshold