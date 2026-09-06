import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from ai_service.config import FACE_DETECTOR_MODEL_PATH


# ==========================================
# FACE DETECTOR
# ==========================================
# Was a bare "face_detector.tflite" (only worked if the process's cwd
# happened to be VERIDEX/). Now resolved from ai_service.config so it
# works regardless of where the app is launched from.

MODEL_PATH = str(FACE_DETECTOR_MODEL_PATH)


def _run_detector(image):

    """
    Run MediaPipe face detection on an image.
    """

    rgb_image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_image
    )

    base_options = python.BaseOptions(
        model_asset_path=MODEL_PATH
    )

    options = vision.FaceDetectorOptions(
        base_options=base_options,
        min_detection_confidence=0.35
    )

    with vision.FaceDetector.create_from_options(
        options
    ) as detector:

        result = detector.detect(mp_image)

    return result


def detect_faces(image_path: str):

    image = cv2.imread(image_path)

    if image is None:
        raise FileNotFoundError(
            f"Could not open image: {image_path}"
        )

    height, width = image.shape[:2]

    results = []

    # ==========================================
    # STEP 1
    # PASSPORT PORTRAIT REGION
    # ==========================================

    #
    # Passport portrait is normally located
    # toward the left side of the data page.
    #
    # We intentionally process this region
    # separately because the full document can
    # contain face-like security patterns.
    #

    roi_width = int(width * 0.45)

    roi_x = 0
    roi_y = int(height * 0.15)

    roi = image[
        roi_y:height,
        roi_x:roi_width
    ]

    # ==========================================
    # UPSCALE PORTRAIT REGION
    # ==========================================

    scale = 2.0

    roi_upscaled = cv2.resize(
        roi,
        None,
        fx=scale,
        fy=scale,
        interpolation=cv2.INTER_CUBIC
    )

    # ==========================================
    # FACE DETECTION ON PORTRAIT REGION
    # ==========================================

    detection_result = _run_detector(
        roi_upscaled
    )

    for detection in detection_result.detections:

        bbox = detection.bounding_box

        # Coordinates are currently relative
        # to the upscaled ROI.
        x = int(bbox.origin_x / scale)
        y = int(bbox.origin_y / scale)

        w = int(bbox.width / scale)
        h = int(bbox.height / scale)

        # Convert ROI coordinates to original
        # passport coordinates.

        x = x + roi_x
        y = y + roi_y

        # ======================================
        # BOUNDARY CHECK
        # ======================================

        x = max(0, min(x, width - 1))
        y = max(0, min(y, height - 1))

        w = min(w, width - x)
        h = min(h, height - y)

        confidence = float(
            detection.categories[0].score
        )

        results.append({
            "x": x,
            "y": y,
            "width": w,
            "height": h,
            "confidence": round(
                confidence,
                4
            )
        })

    # ==========================================
    # STEP 2
    # FULL IMAGE FALLBACK
    # ==========================================

    if not results:

        detection_result = _run_detector(
            image
        )

        for detection in detection_result.detections:

            bbox = detection.bounding_box

            x = max(
                0,
                int(bbox.origin_x)
            )

            y = max(
                0,
                int(bbox.origin_y)
            )

            w = int(bbox.width)
            h = int(bbox.height)

            x = min(
                x,
                width - 1
            )

            y = min(
                y,
                height - 1
            )

            w = min(
                w,
                width - x
            )

            h = min(
                h,
                height - y
            )

            confidence = float(
                detection.categories[0].score
            )

            results.append({
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "confidence": round(
                    confidence,
                    4
                )
            })

    # ==========================================
    # SORT BY CONFIDENCE
    # ==========================================

    results.sort(
        key=lambda f: f["confidence"],
        reverse=True
    )

    return results