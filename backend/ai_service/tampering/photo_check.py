import cv2
import os


# ==================================================
# PHOTO REPLACEMENT DETECTOR
# ==================================================

def analyze_photo_region(image_path: str):
    """
    Analyze the photograph region of a passport.

    This is a heuristic detector designed to identify
    suspicious characteristics around the passport photo.

    It checks:

        1. Whether the image can be loaded
        2. Photo-region dimensions
        3. Sharpness
        4. Edge density
        5. Color variation
        6. Boundary inconsistency

    IMPORTANT:
        These checks do not prove that a photograph
        was replaced. They provide indicators that
        can be combined with other forensic checks.
    """

    # ==================================================
    # CHECK FILE
    # ==================================================

    if not os.path.exists(image_path):

        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    # ==================================================
    # LOAD IMAGE
    # ==================================================

    image = cv2.imread(
        image_path
    )

    if image is None:

        raise ValueError(
            f"Could not read image: {image_path}"
        )

    height, width = image.shape[:2]

    # ==================================================
    # ESTIMATE PASSPORT PHOTO REGION
    # ==================================================

    """
    For the current passport-test layout, the photograph
    is located approximately in the left portion of the
    document.

    We intentionally use a relative region instead of
    hard-coded pixel coordinates so the detector can
    work with different image resolutions.
    """

    x1 = int(width * 0.05)
    x2 = int(width * 0.40)

    y1 = int(height * 0.25)
    y2 = int(height * 0.75)

    photo = image[
        y1:y2,
        x1:x2
    ]

    if photo.size == 0:

        raise ValueError(
            "Could not extract passport photo region."
        )

    # ==================================================
    # PHOTO INFORMATION
    # ==================================================

    photo_height, photo_width = photo.shape[:2]

    # ==================================================
    # GRAYSCALE
    # ==================================================

    gray = cv2.cvtColor(
        photo,
        cv2.COLOR_BGR2GRAY
    )

    # ==================================================
    # SHARPNESS
    # ==================================================

    laplacian = cv2.Laplacian(
        gray,
        cv2.CV_64F
    )

    sharpness = laplacian.var()

    # ==================================================
    # EDGE DENSITY
    # ==================================================

    edges = cv2.Canny(
        gray,
        100,
        200
    )

    edge_pixels = cv2.countNonZero(
        edges
    )

    total_pixels = (
        photo_width *
        photo_height
    )

    edge_ratio = (
        edge_pixels / total_pixels
        if total_pixels > 0
        else 0
    )

    # ==================================================
    # COLOR VARIATION
    # ==================================================

    color_std = cv2.meanStdDev(
        photo
    )[1]

    color_variation = float(
        color_std.mean()
    )

    # ==================================================
    # BOUNDARY ANALYSIS
    # ==================================================

    """
    A replaced photograph may produce an unusual
    boundary between the photograph and the surrounding
    passport background.

    We compare edge activity near the four borders
    of the estimated photo region.
    """

    border_size = max(
        2,
        int(min(
            photo_width,
            photo_height
        ) * 0.05)
    )

    top_border = gray[
        :border_size,
        :
    ]

    bottom_border = gray[
        -border_size:,
        :
    ]

    left_border = gray[
        :,
        :border_size
    ]

    right_border = gray[
        :,
        -border_size:
    ]

    def border_edge_ratio(region):

        if region.size == 0:
            return 0.0

        border_edges = cv2.Canny(
            region,
            100,
            200
        )

        return (
            cv2.countNonZero(
                border_edges
            )
            /
            region.size
        )

    top_ratio = border_edge_ratio(
        top_border
    )

    bottom_ratio = border_edge_ratio(
        bottom_border
    )

    left_ratio = border_edge_ratio(
        left_border
    )

    right_ratio = border_edge_ratio(
        right_border
    )

    boundary_score = (
        top_ratio +
        bottom_ratio +
        left_ratio +
        right_ratio
    ) / 4

    # ==================================================
    # HEURISTIC PHOTO SCORE
    # ==================================================

    photo_score = 0.0

    reasons = []

    # --------------------------------------------------
    # SHARPNESS
    # --------------------------------------------------

    if sharpness < 300:

     photo_score += 25

     reasons.append(
        "Photo region is significantly smoother than expected"
    )

    elif sharpness < 500:

      photo_score += 10

      reasons.append(
        "Photo region has moderately reduced sharpness"
    )

    elif sharpness > 1500:

     photo_score += 15

     reasons.append(
        "Unusually high sharpness in photo region"
    )

# --------------------------------------------------
# EDGE DENSITY
# --------------------------------------------------

    if edge_ratio < 0.015:

      photo_score += 20

      reasons.append(
        "Unusually low edge density in photo region"
    )

    elif edge_ratio > 0.20:

      photo_score += 15

      reasons.append(
        "High edge density in photo region"
    )

    # --------------------------------------------------
    # COLOR VARIATION
    # --------------------------------------------------

    if color_variation > 70:

        photo_score += 10

        reasons.append(
            "Unusual color variation in photo region"
        )

    # --------------------------------------------------
    # BOUNDARY
    # --------------------------------------------------

    if boundary_score > 0.20:

        photo_score += 25

        reasons.append(
            "Strong boundary discontinuity around photo"
        )

    # ==================================================
    # LIMIT SCORE
    # ==================================================

    photo_score = min(
        photo_score,
        100
    )

    # ==================================================
    # STATUS
    # ==================================================

    if photo_score >= 60:

        status = "HIGH_RISK"

    elif photo_score >= 30:

        status = "SUSPICIOUS"

    else:

        status = "LOW_RISK"

    # ==================================================
    # RESULT
    # ==================================================

    return {

        "image": image_path,

        "photoRegion": {

            "x": x1,

            "y": y1,

            "width": x2 - x1,

            "height": y2 - y1
        },

        "analysis": {

            "sharpness": round(
                sharpness,
                2
            ),

            "edgeRatio": round(
                edge_ratio,
                4
            ),

            "colorVariation": round(
                color_variation,
                2
            ),

            "boundaryScore": round(
                boundary_score,
                4
            )
        },

        "photoReplacementScore": round(
            photo_score,
            2
        ),

        "status": status,

        "reasons": reasons
    }