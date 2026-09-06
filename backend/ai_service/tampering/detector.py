import cv2
import os

from ai_service.tampering.metadata import analyze_metadata
from ai_service.tampering.stamp_check import detect_stamp_tampering
from ai_service.tampering.photo_check import analyze_photo_region
from ai_service.tampering.text_check import analyze_text_region


# ==================================================
# IMAGE TAMPERING DETECTOR
# ==================================================

def detect_tampering(image_path: str):
    """
    Perform combined image-forensics analysis on an identity document.

    Checks:
        1. Image loading
        2. Image dimensions
        3. Image quality / sharpness
        4. Edge analysis
        5. High-frequency analysis
        6. ELA-like compression analysis
        7. Metadata analysis
        8. Stamp/seal analysis
        9. Photo replacement analysis
        10. Text manipulation analysis
        11. Combined tampering risk score

    Important:
        This is a heuristic forensic screening system.
        A high score indicates suspicious characteristics,
        but does not by itself prove document forgery.
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

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(
            f"Could not read image: {image_path}"
        )

    # ==================================================
    # IMAGE INFORMATION
    # ==================================================

    height, width = image.shape[:2]

    channels = (
        image.shape[2]
        if len(image.shape) == 3
        else 1
    )

    file_size = os.path.getsize(image_path)

    # ==================================================
    # GRAYSCALE
    # ==================================================

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # ==================================================
    # IMAGE QUALITY / SHARPNESS
    # ==================================================

    laplacian = cv2.Laplacian(
        gray,
        cv2.CV_64F
    )

    sharpness = laplacian.var()

    # ==================================================
    # EDGE ANALYSIS
    # ==================================================

    edges = cv2.Canny(
        gray,
        100,
        200
    )

    edge_pixels = cv2.countNonZero(edges)

    total_pixels = width * height

    edge_ratio = (
        edge_pixels / total_pixels
        if total_pixels > 0
        else 0
    )

    # ==================================================
    # HIGH FREQUENCY ANALYSIS
    # ==================================================

    blurred = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    high_frequency = cv2.absdiff(
        gray,
        blurred
    )

    high_frequency_mean = high_frequency.mean()

    # ==================================================
    # ELA-LIKE ANALYSIS
    # ==================================================

    temp_file = os.path.join(
        os.path.dirname(
            os.path.abspath(image_path)
        ),
        "tampering_temp.jpg"
    )

    cv2.imwrite(
        temp_file,
        image,
        [
            cv2.IMWRITE_JPEG_QUALITY,
            90
        ]
    )

    compressed = cv2.imread(temp_file)

    ela_score = 0.0

    if compressed is not None:

        compressed_gray = cv2.cvtColor(
            compressed,
            cv2.COLOR_BGR2GRAY
        )

        difference = cv2.absdiff(
            gray,
            compressed_gray
        )

        ela_score = difference.mean()

    if os.path.exists(temp_file):
        os.remove(temp_file)

    # ==================================================
    # METADATA ANALYSIS
    # ==================================================

    metadata_result = analyze_metadata(
        image_path
    )

    metadata_score = metadata_result.get(
        "metadataRiskScore",
        0.0
    )

    metadata_reasons = metadata_result.get(
        "reasons",
        []
    )

    # ==================================================
    # STAMP / SEAL ANALYSIS
    # ==================================================

    stamp_result = detect_stamp_tampering(
        image_path
    )

    stamp_regions = stamp_result.get(
        "stamp_regions_detected",
        stamp_result.get(
            "stamp_count",
            0
        )
    )

    stamp_verdict = stamp_result.get(
        "overall_verdict",
        "NO_STAMP_DETECTED"
    )

    stamp_regions_data = stamp_result.get(
        "regions",
        []
    )

    # ==================================================
    # PHOTO REGION ANALYSIS
    # ==================================================

    photo_result = analyze_photo_region(
        image_path
    )

    photo_score = photo_result.get(
        "photoReplacementScore",
        0.0
    )

    # ==================================================
    # TEXT REGION ANALYSIS
    # ==================================================

    text_result = analyze_text_region(
        image_path
    )

    text_score = text_result.get(
        "textManipulationScore",
        0.0
    )

    # ==================================================
    # HEURISTIC RISK SCORE
    # ==================================================

    tampering_score = 0.0
    reasons = []

    # ==================================================
    # PHOTO REPLACEMENT CONTRIBUTION
    # ==================================================

    if photo_score >= 60:

        tampering_score += 40

        reasons.append(
            "Photo region shows strong replacement indicators"
        )

    elif photo_score >= 30:

        tampering_score += 30

        reasons.append(
            "Photo region shows suspicious characteristics"
        )

    elif photo_score >= 15:

        tampering_score += 10

        reasons.append(
            "Photo region shows possible replacement indicators"
        )

    # ==================================================
    # TEXT MANIPULATION CONTRIBUTION
    # ==================================================

    if text_score >= 60:

        tampering_score += 40

        reasons.append(
            "Text region shows strong manipulation indicators"
        )

    elif text_score >= 30:

        tampering_score += 30

        reasons.append(
            "Text region shows suspicious characteristics"
        )

    elif text_score >= 15:

        tampering_score += 10

        reasons.append(
            "Text region shows possible manipulation indicators"
        )

    # ==================================================
    # ELA CONTRIBUTION
    # ==================================================

    if ela_score > 15:

        tampering_score += 30

        reasons.append(
            "High JPEG compression inconsistency"
        )

    elif ela_score > 8:

        tampering_score += 15

        reasons.append(
            "Moderate JPEG compression inconsistency"
        )

    # ==================================================
    # HIGH FREQUENCY CONTRIBUTION
    # ==================================================

    if high_frequency_mean > 18:

        tampering_score += 20

        reasons.append(
            "Unusual high-frequency image regions"
        )

    elif high_frequency_mean > 10:

        tampering_score += 10

        reasons.append(
            "Moderate high-frequency variation"
        )

    # ==================================================
    # EDGE DENSITY CONTRIBUTION
    # ==================================================

    if edge_ratio > 0.20:

        tampering_score += 15

        reasons.append(
            "High edge density"
        )

    # ==================================================
    # SHARPNESS CONTRIBUTION
    # ==================================================

    if sharpness < 50:

        tampering_score += 10

        reasons.append(
            "Low image sharpness"
        )

    # ==================================================
    # METADATA CONTRIBUTION
    # ==================================================

    if metadata_score >= 60:

        tampering_score += 20

        reasons.append(
            "High-risk metadata indicators detected"
        )

    elif metadata_score >= 30:

        tampering_score += 10

        reasons.append(
            "Suspicious metadata indicators detected"
        )

    # ==================================================
    # STAMP CONTRIBUTION
    # ==================================================

    suspicious_stamp_count = 0
    review_stamp_count = 0

    for region in stamp_regions_data:

        verdict = region.get(
            "verdict"
        )

        if verdict == "SUSPICIOUS":

            suspicious_stamp_count += 1

        elif verdict == "REVIEW_RECOMMENDED":

            review_stamp_count += 1

    if suspicious_stamp_count > 0:

        tampering_score += 40

        reasons.append(
            f"{suspicious_stamp_count} stamp/seal region(s) "
            "show strong manipulation indicators"
        )

    elif review_stamp_count > 0:

        tampering_score += 30

        reasons.append(
            f"{review_stamp_count} stamp/seal region(s) "
            "require forensic review"
        )

    # ==================================================
    # ADD METADATA REASONS
    # ==================================================

    for reason in metadata_reasons:

        formatted_reason = (
            f"Metadata: {reason}"
        )

        if formatted_reason not in reasons:

            reasons.append(
                formatted_reason
            )

    # ==================================================
    # ADD STAMP SUMMARY REASON
    # ==================================================

    if stamp_verdict == "SUSPICIOUS":

        reasons.append(
            "Stamp analysis: suspicious stamp/seal "
            "manipulation detected."
        )

    elif stamp_verdict == "REVIEW_RECOMMENDED":

        reasons.append(
            "Stamp analysis: stamp/seal region requires review."
        )

    elif stamp_verdict == "LIKELY_AUTHENTIC":

        reasons.append(
            "Stamp analysis: detected stamp region appears "
            "consistent with an authentic stamp."
        )

    # ==================================================
    # ADD TEXT MODULE REASONS
    # ==================================================

    for reason in text_result.get(
        "reasons",
        []
    ):

        formatted_reason = (
            f"Text analysis: {reason}"
        )

        if formatted_reason not in reasons:

            reasons.append(
                formatted_reason
            )

    # ==================================================
    # ADD PHOTO MODULE REASONS
    # ==================================================

    for reason in photo_result.get(
        "reasons",
        []
    ):

        formatted_reason = (
            f"Photo analysis: {reason}"
        )

        if formatted_reason not in reasons:

            reasons.append(
                formatted_reason
            )

    # ==================================================
    # LIMIT SCORE
    # ==================================================

    tampering_score = min(
        tampering_score,
        100.0
    )

    # ==================================================
    # FINAL DECISION
    # ==================================================

    if tampering_score >= 60:

        status = "HIGH_RISK"

    elif tampering_score >= 30:

        status = "SUSPICIOUS"

    else:

        status = "LOW_RISK"

    # ==================================================
    # RESULT
    # ==================================================

    return {

        "image": image_path,

        "imageInfo": {

            "width": width,
            "height": height,
            "channels": channels,
            "fileSize": file_size
        },

        "analysis": {

            "sharpness": round(
                float(sharpness),
                2
            ),

            "edgeRatio": round(
                float(edge_ratio),
                4
            ),

            "highFrequencyMean": round(
                float(high_frequency_mean),
                2
            ),

            "elaScore": round(
                float(ela_score),
                2
            )
        },

        "metadata": {

            "riskScore": metadata_score,

            "status": metadata_result.get(
                "status",
                "LOW_RISK"
            ),

            "reasons": metadata_reasons,

            "importantMetadata": metadata_result.get(
                "importantMetadata",
                {}
            )
        },

        "stampAnalysis": {

            "regionsDetected": stamp_regions,

            "overallVerdict": stamp_verdict,

            "regions": stamp_regions_data,

            "summary": stamp_result.get(
                "summary",
                ""
            )
        },

        "photoAnalysis": {

            "replacementScore": photo_score,

            "status": photo_result.get(
                "status",
                "LOW_RISK"
            ),

            "photoRegion": photo_result.get(
                "photoRegion",
                {}
            ),

            "analysis": photo_result.get(
                "analysis",
                {}
            ),

            "reasons": photo_result.get(
                "reasons",
                []
            )
        },

        "textAnalysis": {

            "manipulationScore": text_score,

            "status": text_result.get(
                "status",
                "LOW_RISK"
            ),

            "textRegion": text_result.get(
                "textRegion",
                {}
            ),

            "analysis": text_result.get(
                "analysis",
                {}
            ),

            "reasons": text_result.get(
                "reasons",
                []
            )
        },

        "tamperingScore": round(
            float(tampering_score),
            2
        ),

        "status": status,

        "reasons": reasons
    }