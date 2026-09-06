import cv2

from ai_service.ocr.preprocess import preprocess_image


image_path = "sample_data/test_document.png"

processed = preprocess_image(image_path)

cv2.imwrite(
    "output/processed_document.png",
    processed
)

print("Preprocessing completed successfully!")
print("Saved as: processed_document.png")