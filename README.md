# OCR Text Extraction API

A serverless API built with FastAPI that extracts text from images using Tesseract OCR.

## Features
- Extract text from JPG, PNG, and GIF images
- Confidence scoring for extracted text
- Image metadata extraction
- Rate limiting (5 requests/minute per IP)
- In-memory caching for duplicate images
- Batch processing (up to 5 images)

## Quick Start
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
curl http://localhost:8080/
```
