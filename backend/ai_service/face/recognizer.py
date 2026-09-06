import cv2
import numpy as np

from ai_service.config import FACE_RECOGNIZER_MODEL_PATH


# Was a bare filename that only resolved if cwd == VERIDEX/. Now
# resolved from ai_service.config (models/ dir, env-overridable).
MODEL_PATH = str(FACE_RECOGNIZER_MODEL_PATH)


class FaceRecognizer:

    def __init__(self, model_path=MODEL_PATH):

        if not hasattr(cv2, "FaceRecognizerSF_create"):
            raise RuntimeError(
                "Your OpenCV installation does not provide "
                "FaceRecognizerSF_create."
            )

        self.model = cv2.FaceRecognizerSF_create(
            model_path,
            ""
        )

    def get_feature(self, image_path: str):

        image = cv2.imread(image_path)

        if image is None:
            raise FileNotFoundError(
                f"Could not open image: {image_path}"
            )

        # SFace expects a detected/aligned face.
        # passport_face.png is already cropped.
        feature = self.model.feature(image)

        return feature

    def compare(self, feature1, feature2):

        cosine_score = self.model.match(
            feature1,
            feature2,
            cv2.FaceRecognizerSF_FR_COSINE
        )

        return float(cosine_score)


def compare_faces(
    passport_face_path: str,
    user_face_path: str
):

    recognizer = FaceRecognizer()

    passport_feature = recognizer.get_feature(
        passport_face_path
    )

    user_feature = recognizer.get_feature(
        user_face_path
    )

    similarity = recognizer.compare(
        passport_feature,
        user_feature
    )

    # Initial development threshold, now overridable via
    # VERIDEX_FACE_MATCH_THRESHOLD instead of a buried literal.
    from ai_service.config import FACE_MATCH_THRESHOLD as threshold

    matched = similarity >= threshold

    return {
        "similarity": round(similarity, 4),
        "threshold": threshold,
        "matched": matched
    }