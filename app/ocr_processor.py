# app/ocr_processor.py
import io
import pytesseract
from PIL import Image

def process_image_with_ocr(image_bytes: bytes) -> str:
    try:
        image = Image.open(io.BytesIO(image_bytes))
        grayscale_image = image.convert('L')
        extracted_text = pytesseract.image_to_string(grayscale_image, lang='eng')
        return extracted_text.strip()
    except Exception as e:
        print(f"An error occurred during OCR processing: {e}")
        return ""