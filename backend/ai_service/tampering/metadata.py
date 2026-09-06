import os
from PIL import Image
from PIL.ExifTags import TAGS


# ==================================================
# METADATA ANALYSIS
# ==================================================

def analyze_metadata(image_path: str) -> dict:
    """
    Analyze image metadata for possible tampering indicators.

    Checks:
        - File existence
        - Image format
        - Image dimensions
        - EXIF metadata
        - Camera information
        - Software/editing information
        - Date/time metadata

    Metadata anomalies contribute to a risk assessment,
    but metadata alone does NOT prove forgery.
    """

    # ==================================================
    # CHECK FILE
    # ==================================================

    if not os.path.exists(image_path):

        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    # ==================================================
    # OPEN IMAGE
    # ==================================================

    try:

        image = Image.open(
            image_path
        )

    except Exception as e:

        raise ValueError(
            f"Could not read image: {e}"
        )

    # ==================================================
    # BASIC INFORMATION
    # ==================================================

    file_size = os.path.getsize(
        image_path
    )

    image_format = image.format

    width, height = image.size

    # ==================================================
    # EXIF
    # ==================================================

    exif_data = {}

    try:

        raw_exif = image.getexif()

        for tag_id, value in raw_exif.items():

            tag_name = TAGS.get(
                tag_id,
                str(tag_id)
            )

            # Convert values that may not
            # serialize cleanly

            try:

                exif_data[tag_name] = str(
                    value
                )

            except Exception:

                exif_data[tag_name] = (
                    "<unreadable>"
                )

    except Exception:

        exif_data = {}

    # ==================================================
    # IMPORTANT METADATA
    # ==================================================

    software = exif_data.get(
        "Software",
        ""
    )

    camera_make = exif_data.get(
        "Make",
        ""
    )

    camera_model = exif_data.get(
        "Model",
        ""
    )

    date_time = exif_data.get(
        "DateTime",
        ""
    )

    date_time_original = exif_data.get(
        "DateTimeOriginal",
        ""
    )

    # ==================================================
    # RISK ANALYSIS
    # ==================================================

    risk_score = 0

    reasons = []

    # --------------------------------------------------
    # Software metadata
    # --------------------------------------------------

    if software:

        software_lower = software.lower()

        editing_keywords = [
            "photoshop",
            "gimp",
            "paint",
            "canva",
            "adobe",
            "lightroom",
            "snapseed",
            "pixlr"
        ]

        if any(
            keyword in software_lower
            for keyword in editing_keywords
        ):

            risk_score += 30

            reasons.append(
                "Image contains editing software metadata."
            )

    # --------------------------------------------------
    # Missing EXIF
    # --------------------------------------------------

    if not exif_data:

        reasons.append(
            "No EXIF metadata found."
        )

    # --------------------------------------------------
    # Unusual dimensions
    # --------------------------------------------------

    if width < 300 or height < 200:

        risk_score += 10

        reasons.append(
            "Image resolution is unusually low."
        )

    # --------------------------------------------------
    # Very large image
    # --------------------------------------------------

    if width > 5000 or height > 5000:

        risk_score += 5

        reasons.append(
            "Image resolution is unusually high."
        )

    # ==================================================
    # LIMIT SCORE
    # ==================================================

    risk_score = min(
        risk_score,
        100
    )

    # ==================================================
    # STATUS
    # ==================================================

    if risk_score >= 60:

        status = "HIGH_RISK"

    elif risk_score >= 30:

        status = "SUSPICIOUS"

    else:

        status = "LOW_RISK"

    # ==================================================
    # RESULT
    # ==================================================

    return {

        "file": image_path,

        "fileInfo": {

            "format": image_format,

            "width": width,

            "height": height,

            "fileSize": file_size
        },

        "exif": exif_data,

        "importantMetadata": {

            "software": software,

            "cameraMake": camera_make,

            "cameraModel": camera_model,

            "dateTime": date_time,

            "dateTimeOriginal":
                date_time_original
        },

        "metadataRiskScore": risk_score,

        "status": status,

        "reasons": reasons
    }