# app/ocr_processor.py

import io
import pytesseract
from PIL import Image
from pytesseract import Output

def process_image_with_ocr(image_bytes: bytes) -> tuple[str, float | None]:
    """
    Processes image bytes using Tesseract OCR, extracting text and average confidence.

    Args:
        image_bytes: The raw byte content of the image.

    Returns:
        A tuple containing:
        - The extracted text as a single string.
        - The average confidence score (0-100) of all recognized words, or None.
     especialista"""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        
        # Preprocessing: Convert to grayscale
        grayscale_image = image.convert('L')

        # Use image_to_data to get detailed information, including confidence scores
        ocr_data = pytesseract.image_to_data(grayscale_image, lang='eng', output_type=Output.DICT)
        
        words = []
        confidences = []
        
        num_boxes = len(ocr_data['level'])
        for i in range(num_boxes):
            # Tesseract's confidence is on a scale of 0-100.
            # A value of -1 indicates a non-text block (e.g., whitespace).
            # We only consider words with a confidence score > 0.
            confidence = int(ocr_data['conf'][i])
            if confidence > 0:
                word = ocr_data['text'][i].strip()
                if word: # Ensure the word is not just empty space
                    words.append(word)
                    confidences.append(confidence)

        if not words:
            return "", None

        full_text = " ".join(words)
        average_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return full_text, round(average_confidence, 2)

    except Exception as e:
        print(f"An error occurred during OCR processing: {e}")
        return "", None