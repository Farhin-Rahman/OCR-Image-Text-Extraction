# app/ocr_processor.py

import io
import re
import pytesseract
from PIL import Image
from pytesseract import Output
from typing import Tuple, Optional

def preprocess_text(text: str) -> str:
    """
    Clean and format extracted text for better readability.
    
    Args:
        text: Raw text extracted from OCR
        
    Returns:
        Cleaned and formatted text
    """
    if not text:
        return ""
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Fix common OCR mistakes
    replacements = {
        ' , ': ', ',
        ' . ': '. ',
        ' ! ': '! ',
        ' ? ': '? ',
        ' : ': ': ',
        ' ; ': '; ',
        '( ': '(',
        ' )': ')',
        '[ ': '[',
        ' ]': ']',
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Capitalize first letter after sentences
    text = re.sub(r'(?<=[.!?])\s+([a-z])', lambda m: ' ' + m.group(1).upper(), text)
    
    # Remove spaces before punctuation
    text = re.sub(r'\s+([,.!?;:])', r'\1', text)
    
    # Add space after punctuation if missing
    text = re.sub(r'([,.!?;:])([A-Za-z])', r'\1 \2', text)
    
    # Trim whitespace
    text = text.strip()
    
    # Ensure first letter is capitalized
    if text and text[0].isalpha():
        text = text[0].upper() + text[1:]
    
    return text

def process_image_with_ocr(image_bytes: bytes) -> Tuple[str, Optional[float]]:
    """
    Processes image bytes using Tesseract OCR, extracting text and average confidence.

    Args:
        image_bytes: The raw byte content of the image.

    Returns:
        A tuple containing:
        - The extracted text as a single string (preprocessed).
        - The average confidence score (0-100) of all recognized words, or None.
    """
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

        # Join words and apply preprocessing
        raw_text = " ".join(words)
        cleaned_text = preprocess_text(raw_text)
        
        average_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return cleaned_text, round(average_confidence, 2)

    except Exception as e:
        print(f"An error occurred during OCR processing: {e}")
        return "", None
