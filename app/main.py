# app/main.py

import time
import hashlib
from typing import List
import asyncio
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from starlette.status import HTTP_413_REQUEST_ENTITY_TOO_LARGE, HTTP_415_UNSUPPORTED_MEDIA_TYPE, HTTP_429_TOO_MANY_REQUESTS
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from PIL import Image
import io

from . import ocr_processor

# --- Configuration ---
MAX_FILE_SIZE = 10 * 1024 * 1024
# BONUS: Support for multiple image formats
ACCEPTED_FILE_TYPES = ["image/jpeg", "image/png", "image/gif"]

# --- Feature Implementations ---

# BONUS: Rate Limiting (5 requests per minute per IP)
limiter = Limiter(key_func=get_remote_address)

# BONUS: Caching (simple in-memory cache)
# In a production app, you'd use Redis or a similar persistent cache.
_cache = {}

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Enhanced OCR API",
    description="A serverless API to extract text and metadata from images, with rate limiting and caching.",
    version="2.0.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- API Endpoints ---
@app.get("/", tags=["Health Check"])
async def read_root():
    """A simple health check endpoint."""
    return {"status": "ok", "message": "Enhanced OCR API is running!"}

@app.get("/health", tags=["Health Check"])
async def health_check():
    """Health check for deployment platforms"""
    return {"status": "healthy"}

@app.post("/extract-text", tags=["OCR"])
@limiter.limit("5/minute")
async def extract_text_from_image(request: Request, image: UploadFile = File(...)):
    """
    Accepts an image (JPG, PNG, GIF), validates it, and extracts text,
    confidence score, and metadata. Caches results for identical images.
    """
    start_time = time.time()

    # --- 1. Validate File Type ---
    if image.content_type not in ACCEPTED_FILE_TYPES:
        raise HTTPException(
            status_code=HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported format. Supported formats are: {', '.join(ACCEPTED_FILE_TYPES)}"
        )

    # --- 2. Validate File Size & Read Content ---
    contents = await image.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds the limit of 10MB."
        )

    # --- 3. Caching Logic ---
    image_hash = hashlib.sha256(contents).hexdigest()
    if image_hash in _cache:
        cached_result = _cache[image_hash].copy()  # Use copy() to avoid modifying cache
        cached_result["processing_time_ms"] = round((time.time() - start_time) * 1000)
        cached_result["cached"] = True
        return cached_result

    # --- 4. Process the image (if not cached) ---
    extracted_text, confidence = ocr_processor.process_image_with_ocr(contents)

    # --- 5. Extract Image Metadata ---
    try:
        pil_image = Image.open(io.BytesIO(contents))
        metadata = {
            "filename": image.filename,
            "content_type": image.content_type,
            "width": pil_image.width,
            "height": pil_image.height,
            "format": pil_image.format,
            "mode": pil_image.mode,
            "size_bytes": len(contents)
        }
    except Exception:
        metadata = {"error": "Could not extract metadata."}

    processing_time_ms = round((time.time() - start_time) * 1000)

    # --- 6. Format the response ---
    if not extracted_text:
        response_data = {
            "success": True,
            "message": "No text found in the image.",
            "text": "",
            "confidence": None,
            "metadata": metadata,
            "processing_time_ms": processing_time_ms,
            "cached": False
        }
    else:
        response_data = {
            "success": True,
            "text": extracted_text,
            "confidence": confidence,
            "metadata": metadata,
            "processing_time_ms": processing_time_ms,
            "cached": False
        }

    # Store the result in the cache before returning
    _cache[image_hash] = response_data.copy()
    
    return response_data

@app.post("/batch-extract", tags=["OCR"])
@limiter.limit("2/minute")  # Lower rate limit for batch operations
async def batch_extract_text(request: Request, images: List[UploadFile] = File(...)):
    """
    Batch process multiple images and extract text from each.
    Maximum 5 images per request.
    """
    start_time = time.time()
    
    # Validate number of files
    if len(images) > 5:
        raise HTTPException(
            status_code=400,
            detail="Maximum 5 images allowed per batch request"
        )
    
    # Process all images concurrently
    async def process_single_image(image: UploadFile, index: int):
        try:
            # Validate file type
            if image.content_type not in ACCEPTED_FILE_TYPES:
                return {
                    "index": index,
                    "filename": image.filename,
                    "success": False,
                    "error": f"Unsupported format. Supported formats are: {', '.join(ACCEPTED_FILE_TYPES)}"
                }
            
            # Read and validate size
            contents = await image.read()
            if len(contents) > MAX_FILE_SIZE:
                return {
                    "index": index,
                    "filename": image.filename,
                    "success": False,
                    "error": "File size exceeds the limit of 10MB."
                }
            
            # Check cache
            image_hash = hashlib.sha256(contents).hexdigest()
            if image_hash in _cache:
                cached_result = _cache[image_hash].copy()
                return {
                    "index": index,
                    "filename": image.filename,
                    "success": True,
                    "text": cached_result.get("text", ""),
                    "confidence": cached_result.get("confidence"),
                    "cached": True
                }
            
            # Process with OCR
            extracted_text, confidence = ocr_processor.process_image_with_ocr(contents)
            
            # Cache the result
            result = {
                "text": extracted_text,
                "confidence": confidence
            }
            _cache[image_hash] = result
            
            return {
                "index": index,
                "filename": image.filename,
                "success": True,
                "text": extracted_text if extracted_text else "",
                "confidence": confidence,
                "cached": False,
                "message": "No text found in the image." if not extracted_text else None
            }
            
        except Exception as e:
            return {
                "index": index,
                "filename": image.filename,
                "success": False,
                "error": str(e)
            }
    
    # Process all images concurrently
    tasks = [process_single_image(image, i) for i, image in enumerate(images)]
    results = await asyncio.gather(*tasks)
    
    processing_time_ms = round((time.time() - start_time) * 1000)
    
    # Count successes
    successful = sum(1 for r in results if r["success"])
    
    return {
        "success": True,
        "total_images": len(images),
        "successful": successful,
        "failed": len(images) - successful,
        "processing_time_ms": processing_time_ms,
        "results": results
    }
