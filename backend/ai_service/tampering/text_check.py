import cv2
import numpy as np
import os
import statistics


# ============================================================
# TEXT MANIPULATION / TAMPERING DETECTOR
# ============================================================
#
# Prototype heuristic detector for detecting suspiciously
# edited/retyped text regions in identity documents.
#
# Main signals:
#   1. Local sharpness discontinuity
#   2. Local texture discontinuity
#   3. Rectangular editing/seam boundaries
#   4. Local contrast mismatch
#   5. High-frequency artifacts
#
# IMPORTANT:
# This is a heuristic detector, not a forensic guarantee.
#


# ============================================================
# CONFIGURATION
# ============================================================

TEXT_X1 = 0.35
TEXT_X2 = 0.95
TEXT_Y1 = 0.20
TEXT_Y2 = 0.65

GRID_ROWS = 8
GRID_COLS = 8

# Score thresholds
SUSPICIOUS_THRESHOLD = 30.0
HIGH_RISK_THRESHOLD = 60.0


# ============================================================
# HELPER: SAFE FLOAT
# ============================================================

def _safe_float(value):
    try:
        return float(value)
    except Exception:
        return 0.0


# ============================================================
# HELPER: LOCAL BLOCK ANALYSIS
# ============================================================

def _analyze_blocks(gray):
    """
    Divide the text region into an 8x8 grid and calculate
    local statistics for each block.
    """

    height, width = gray.shape[:2]

    block_height = max(1, height // GRID_ROWS)
    block_width = max(1, width // GRID_COLS)

    blocks = []

    for r in range(GRID_ROWS):

        for c in range(GRID_COLS):

            y1 = r * block_height

            y2 = (
                (r + 1) * block_height
                if r < GRID_ROWS - 1
                else height
            )

            x1 = c * block_width

            x2 = (
                (c + 1) * block_width
                if c < GRID_COLS - 1
                else width
            )

            block = gray[y1:y2, x1:x2]

            if block.size == 0:
                continue

            laplacian = float(
                cv2.Laplacian(
                    block,
                    cv2.CV_64F
                ).var()
            )

            mean_value = float(block.mean())

            std_value = float(block.std())

            blur = cv2.GaussianBlur(
                block,
                (5, 5),
                0
            )

            high_freq = float(
                cv2.absdiff(
                    block,
                    blur
                ).mean()
            )

            blocks.append({
                "row": r,
                "col": c,
                "sharpness": laplacian,
                "mean": mean_value,
                "std": std_value,
                "highFrequency": high_freq
            })

    return blocks


# ============================================================
# HELPER: NEIGHBOR DIFFERENCE
# ============================================================

def _neighbor_differences(blocks):
    """
    Compare each block against neighboring blocks.

    This is more useful than simply asking whether a block
    has high sharpness.

    A genuine scanned document can have high sharpness
    everywhere. A digitally edited region is more likely
    to create a sudden local discontinuity.
    """

    lookup = {
        (b["row"], b["col"]): b
        for b in blocks
    }

    sharpness_diffs = []
    mean_diffs = []
    texture_diffs = []

    suspicious_blocks = []

    for block in blocks:

        r = block["row"]
        c = block["col"]

        neighbors = []

        positions = [
            (r - 1, c),
            (r + 1, c),
            (r, c - 1),
            (r, c + 1)
        ]

        for position in positions:

            if position in lookup:
                neighbors.append(
                    lookup[position]
                )

        if not neighbors:
            continue

        neighbor_sharpness = [
            n["sharpness"]
            for n in neighbors
        ]

        neighbor_mean = [
            n["mean"]
            for n in neighbors
        ]

        neighbor_texture = [
            n["highFrequency"]
            for n in neighbors
        ]

        local_sharpness_reference = statistics.mean(
            neighbor_sharpness
        )

        local_mean_reference = statistics.mean(
            neighbor_mean
        )

        local_texture_reference = statistics.mean(
            neighbor_texture
        )

        sharpness_reference = max(
            local_sharpness_reference,
            1.0
        )

        texture_reference = max(
            local_texture_reference,
            0.5
        )

        sharpness_difference = abs(
            block["sharpness"] -
            local_sharpness_reference
        ) / sharpness_reference

        mean_difference = abs(
            block["mean"] -
            local_mean_reference
        )

        texture_difference = abs(
            block["highFrequency"] -
            local_texture_reference
        ) / texture_reference

        sharpness_diffs.append(
            sharpness_difference
        )

        mean_diffs.append(
            mean_difference
        )

        texture_diffs.append(
            texture_difference
        )

        # ----------------------------------------------------
        # LOCAL SUSPICION
        # ----------------------------------------------------
        #
        # Require more than one abnormal characteristic.
        # This avoids treating normal printed text as edited
        # simply because it is sharp.
        # ----------------------------------------------------

        abnormal_signals = 0

        if sharpness_difference > 1.5:
            abnormal_signals += 1

        if mean_difference > 12:
            abnormal_signals += 1

        if texture_difference > 1.5:
            abnormal_signals += 1

        if abnormal_signals >= 2:

            suspicious_blocks.append({
                "row": r,
                "col": c,
                "sharpnessDifference": round(
                    sharpness_difference,
                    4
                ),
                "meanDifference": round(
                    mean_difference,
                    4
                ),
                "textureDifference": round(
                    texture_difference,
                    4
                )
            })

    if sharpness_diffs:
        mean_sharpness_difference = statistics.mean(
            sharpness_diffs
        )
    else:
        mean_sharpness_difference = 0.0

    if mean_diffs:
        mean_intensity_difference = statistics.mean(
            mean_diffs
        )
    else:
        mean_intensity_difference = 0.0

    if texture_diffs:
        mean_texture_difference = statistics.mean(
            texture_diffs
        )
    else:
        mean_texture_difference = 0.0

    return {
        "meanSharpnessDifference":
            mean_sharpness_difference,

        "meanIntensityDifference":
            mean_intensity_difference,

        "meanTextureDifference":
            mean_texture_difference,

        "suspiciousBlocks":
            suspicious_blocks
    }


# ============================================================
# HELPER: RECTANGULAR SEAM DETECTION
# ============================================================

def _detect_rectangular_seam(gray):
    """
    Look for strong horizontal/vertical boundaries.

    Digital copy/paste editing can leave a rectangular seam
    around the modified area.

    We do not flag a single strong edge. Several aligned
    boundaries are required.
    """

    blurred = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    gradient_x = cv2.Sobel(
        blurred,
        cv2.CV_64F,
        1,
        0,
        ksize=3
    )

    gradient_y = cv2.Sobel(
        blurred,
        cv2.CV_64F,
        0,
        1,
        ksize=3
    )

    abs_x = np.abs(gradient_x)
    abs_y = np.abs(gradient_y)

    height, width = gray.shape[:2]

    # --------------------------------------------------------
    # Ignore very small borders
    # --------------------------------------------------------

    margin_y = max(5, int(height * 0.08))
    margin_x = max(5, int(width * 0.08))

    center = gray[
        margin_y:height - margin_y,
        margin_x:width - margin_x
    ]

    if center.size == 0:
        return {
            "seamScore": 0.0,
            "strongHorizontal": 0,
            "strongVertical": 0
        }

    center_x = abs_x[
        margin_y:height - margin_y,
        margin_x:width - margin_x
    ]

    center_y = abs_y[
        margin_y:height - margin_y,
        margin_x:width - margin_x
    ]

    # --------------------------------------------------------
    # Robust thresholds based on the image itself
    # --------------------------------------------------------

    x_threshold = max(
        18.0,
        float(np.percentile(center_x, 98))
    )

    y_threshold = max(
        18.0,
        float(np.percentile(center_y, 98))
    )

    strong_x = center_x > x_threshold
    strong_y = center_y > y_threshold

    # --------------------------------------------------------
    # Calculate concentration of strong gradients
    # --------------------------------------------------------

    vertical_profile = strong_x.mean(axis=0)

    horizontal_profile = strong_y.mean(axis=1)

    strong_vertical = int(
        np.sum(
            vertical_profile > 0.12
        )
    )

    strong_horizontal = int(
        np.sum(
            horizontal_profile > 0.12
        )
    )

    # --------------------------------------------------------
    # Seam score
    # --------------------------------------------------------

    seam_score = 0.0

    if strong_vertical >= 2:
        seam_score += 15

    if strong_horizontal >= 2:
        seam_score += 15

    # Stronger evidence when both directions exist
    if (
        strong_vertical >= 2
        and strong_horizontal >= 2
    ):
        seam_score += 15

    return {
        "seamScore": min(
            float(seam_score),
            45.0
        ),

        "strongHorizontal":
            strong_horizontal,

        "strongVertical":
            strong_vertical
    }


# ============================================================
# MAIN FUNCTION
# ============================================================

def analyze_text_region(image_path: str):
    """
    Analyze the estimated document text region.

    Returns:
        dict
    """

    # --------------------------------------------------------
    # LOAD IMAGE
    # --------------------------------------------------------

    image = cv2.imread(image_path)

    if image is None:
        raise FileNotFoundError(
            f"Could not load image: {image_path}"
        )

    height, width = image.shape[:2]

    # --------------------------------------------------------
    # TEXT REGION
    # --------------------------------------------------------

    x1 = int(width * TEXT_X1)
    x2 = int(width * TEXT_X2)

    y1 = int(height * TEXT_Y1)
    y2 = int(height * TEXT_Y2)

    text_region = image[
        y1:y2,
        x1:x2
    ]

    if text_region.size == 0:

        return {
            "image": image_path,

            "textRegion": {
                "x": x1,
                "y": y1,
                "width": x2 - x1,
                "height": y2 - y1
            },

            "analysis": {},

            "textManipulationScore": 0.0,

            "status": "LOW_RISK",

            "reasons": [
                "Text region could not be analyzed."
            ]
        }

    # --------------------------------------------------------
    # GRAYSCALE
    # --------------------------------------------------------

    gray = cv2.cvtColor(
        text_region,
        cv2.COLOR_BGR2GRAY
    )

    # --------------------------------------------------------
    # GLOBAL SHARPNESS
    # --------------------------------------------------------

    sharpness = float(
        cv2.Laplacian(
            gray,
            cv2.CV_64F
        ).var()
    )

    # --------------------------------------------------------
    # EDGE RATIO
    # --------------------------------------------------------

    edges = cv2.Canny(
        gray,
        100,
        200
    )

    total_pixels = (
        gray.shape[0] *
        gray.shape[1]
    )

    edge_pixels = cv2.countNonZero(
        edges
    )

    edge_ratio = (
        edge_pixels / total_pixels
        if total_pixels > 0
        else 0.0
    )

    # --------------------------------------------------------
    # INTENSITY
    # --------------------------------------------------------

    intensity_mean = float(
        gray.mean()
    )

    intensity_std = float(
        gray.std()
    )

    # --------------------------------------------------------
    # HIGH FREQUENCY
    # --------------------------------------------------------

    blurred = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    high_frequency = cv2.absdiff(
        gray,
        blurred
    )

    high_frequency_mean = float(
        high_frequency.mean()
    )

    # --------------------------------------------------------
    # LOCAL BLOCK ANALYSIS
    # --------------------------------------------------------

    blocks = _analyze_blocks(
        gray
    )

    block_sharpness = [
        b["sharpness"]
        for b in blocks
    ]

    block_means = [
        b["mean"]
        for b in blocks
    ]

    if block_sharpness:

        block_mean = float(
            statistics.mean(
                block_sharpness
            )
        )

        block_variation = float(
            statistics.pstdev(
                block_sharpness
            )
        )

    else:

        block_mean = 0.0
        block_variation = 0.0

    if block_mean > 0:

        consistency_ratio = (
            block_variation /
            block_mean
        )

    else:

        consistency_ratio = 0.0

    # --------------------------------------------------------
    # NEIGHBOR COMPARISON
    # --------------------------------------------------------

    neighbor_result = _neighbor_differences(
        blocks
    )

    mean_sharpness_difference = (
        neighbor_result[
            "meanSharpnessDifference"
        ]
    )

    mean_intensity_difference = (
        neighbor_result[
            "meanIntensityDifference"
        ]
    )

    mean_texture_difference = (
        neighbor_result[
            "meanTextureDifference"
        ]
    )

    suspicious_blocks = (
        neighbor_result[
            "suspiciousBlocks"
        ]
    )

    anomalous_blocks = len(
        suspicious_blocks
    )

    if blocks:

        local_anomaly_score = (
            anomalous_blocks /
            len(blocks)
        )

    else:

        local_anomaly_score = 0.0

    # --------------------------------------------------------
    # RECTANGULAR SEAM
    # --------------------------------------------------------

    seam_result = _detect_rectangular_seam(
        gray
    )

    seam_score = seam_result[
        "seamScore"
    ]

    # ========================================================
    # TAMPERING SCORE
    # ========================================================

    score = 0.0
    reasons = []

    # --------------------------------------------------------
    # 1. GLOBAL SHARPNESS
    # --------------------------------------------------------
    #
    # IMPORTANT:
    # Do NOT treat high sharpness alone as tampering.
    #
    # Printed text can naturally be sharp.
    # --------------------------------------------------------

    if sharpness > 5000:

        score += 5

        reasons.append(
            "Extremely high text-region sharpness."
        )

    # --------------------------------------------------------
    # 2. HIGH-FREQUENCY ARTIFACTS
    # --------------------------------------------------------

    if high_frequency_mean > 18:

        score += 10

        reasons.append(
            "Strong high-frequency artifacts detected."
        )

    # --------------------------------------------------------
    # 3. LOCAL SHARPNESS DISCONTINUITY
    # --------------------------------------------------------

    if mean_sharpness_difference > 2.0:

        score += 15

        reasons.append(
            "Strong local sharpness discontinuity detected."
        )

    elif mean_sharpness_difference > 1.3:

        score += 8

        reasons.append(
            "Moderate local sharpness discontinuity detected."
        )

    # --------------------------------------------------------
    # 4. LOCAL INTENSITY DISCONTINUITY
    # --------------------------------------------------------

    if mean_intensity_difference > 20:

        score += 15

        reasons.append(
            "Strong local intensity mismatch detected."
        )

    elif mean_intensity_difference > 12:

        score += 8

        reasons.append(
            "Moderate local intensity mismatch detected."
        )

    # --------------------------------------------------------
    # 5. LOCAL TEXTURE DISCONTINUITY
    # --------------------------------------------------------

    if mean_texture_difference > 2.5:

        score += 15

        reasons.append(
            "Strong local texture discontinuity detected."
        )

    elif mean_texture_difference > 1.7:

        score += 8

        reasons.append(
            "Moderate local texture discontinuity detected."
        )

    # --------------------------------------------------------
    # 6. SUSPICIOUS BLOCKS
    # --------------------------------------------------------

    if anomalous_blocks >= 6:

        score += 20

        reasons.append(
            f"{anomalous_blocks} locally inconsistent "
            "text blocks detected."
        )

    elif anomalous_blocks >= 3:

        score += 10

        reasons.append(
            f"{anomalous_blocks} locally inconsistent "
            "text blocks detected."
        )

        # --------------------------------------------------------
    # 7. RECTANGULAR SEAM
    # --------------------------------------------------------
    # --------------------------------------------------------
    
    if seam_score >= 30:

        score += 40

        reasons.append(
            "Strong rectangular editing boundary detected."
        )

    elif seam_score >= 15:

        score += 5

        reasons.append(
            "Possible rectangular editing boundary detected."
        )

    # --------------------------------------------------------
    # CAP
    # --------------------------------------------------------

    score = min(
        float(score),
        100.0
    )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    if score >= HIGH_RISK_THRESHOLD:

        status = "HIGH_RISK"

    elif score >= SUSPICIOUS_THRESHOLD:

        status = "SUSPICIOUS"

    else:

        status = "LOW_RISK"

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {
        "image": image_path,

        "textRegion": {
            "x": x1,
            "y": y1,
            "width": x2 - x1,
            "height": y2 - y1
        },

        "analysis": {

            "sharpness":
                round(sharpness, 4),

            "edgeRatio":
                round(edge_ratio, 4),

            "intensityMean":
                round(intensity_mean, 4),

            "intensityStd":
                round(intensity_std, 4),

            "highFrequency":
                round(
                    high_frequency_mean,
                    4
                ),

            "blockMean":
                round(
                    block_mean,
                    4
                ),

            "blockVariation":
                round(
                    block_variation,
                    4
                ),

            "consistencyRatio":
                round(
                    consistency_ratio,
                    4
                ),

            "anomalousBlocks":
                anomalous_blocks,

            "localAnomalyScore":
                round(
                    local_anomaly_score,
                    4
                ),

            "localTexture":
                round(
                    block_mean,
                    4
                ),

            "neighborSharpnessDifference":
                round(
                    mean_sharpness_difference,
                    4
                ),

            "neighborIntensityDifference":
                round(
                    mean_intensity_difference,
                    4
                ),

            "neighborTextureDifference":
                round(
                    mean_texture_difference,
                    4
                ),

            "seamScore":
                round(
                    seam_score,
                    4
                ),

            "strongHorizontalSeams":
                seam_result[
                    "strongHorizontal"
                ],

            "strongVerticalSeams":
                seam_result[
                    "strongVertical"
                ]
        },

        "textManipulationScore":
            round(
                score,
                2
            ),

        "status":
            status,

        "reasons":
            reasons
    }


# ============================================================
# STANDALONE COMMAND-LINE TEST
# ============================================================

if __name__ == "__main__":

    import sys

    if len(sys.argv) < 2:

        print(
            "Usage:"
        )

        print(
            "python text_check.py <image_path>"
        )

        sys.exit(1)

    image_path = sys.argv[1]

    result = analyze_text_region(
        image_path
    )

    print("=" * 70)
    print("TEXT TAMPERING ANALYSIS")
    print("=" * 70)

    print(
        f"Image                 : "
        f"{result['image']}"
    )

    print(
        f"Status                : "
        f"{result['status']}"
    )

    print(
        f"textManipulationScore : "
        f"{result['textManipulationScore']}"
    )

    print(
        f"textRegion            : "
        f"{result['textRegion']}"
    )

    print("\nAnalysis:")

    for key, value in result[
        "analysis"
    ].items():

        print(
            f"  {key}: {value}"
        )

    print("\nReasons:")

    if result["reasons"]:

        for reason in result["reasons"]:

            print(
                f"  - {reason}"
            )

    else:

        print(
            "  (none)"
        )