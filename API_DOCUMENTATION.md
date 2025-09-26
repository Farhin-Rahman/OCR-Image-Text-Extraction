# OCR API Documentation

## Base URL
[Will be updated after deployment]

## Endpoints

1. GET / - Health check
2. POST /extract-text - Extract text from single image
3. POST /batch-extract - Extract text from multiple images

## Example Usage
```bash
curl -X POST -F "image=@test.jpg" https://your-url/extract-text

