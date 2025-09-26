# Paste this code into the app/main.py EDITOR window

import time
from fastapi import FastAPI, File, UploadFile, HTTPException
from starlette.status import HTTP_413_REQUEST_ENTITY_TOO_LARGE, HTTP_415_UNSUPPORTED_MEDIA_TYPE
from . import ocr_processor

MAX_FILE_SIZE = 10 * 1024 * 1024
ACCEPTED_FILE_TYPES = ["image/jpeg"]

app = FastAPI(
    title="OCR API",
    description="A serverless API to extract text from JPG images using Tesseract OCR.",
    version="1.0.0"
)

@app.get("/", tags=["Health Check"])
async def read_root():
    return {"status": "ok", "message": "OCR API is running!"}

@app.post("/extract-text", tags=["OCR"])
async def extract_text_from_image(image: UploadFile = File(...)):
    start_time = time.time()
    if image.content_type not in ACCEPTED_FILE_TYPES:
        raise HTTPException(status_code=HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported file format. Only JPG/JPEG is allowed.")
    contents = await image.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File size exceeds the limit of 10MB.")
    
    extracted_text = ocr_processor.process_image_with_ocr(contents)
    processing_time_ms = round((time.time() - start_time) * 1000)

    if not extracted_text:
        return {
            "success": True, "text": "", "message": "No text found in the image.",
            "confidence": None, "processing_time_ms": processing_time_ms
        }
    return {
        "success": True, "text": extracted_text, "confidence": None,
        "processing_time_ms": processing_time_ms
    }