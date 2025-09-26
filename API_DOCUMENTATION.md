# OCR API Documentation

## Base URL
https://helpful-balance-production-e085.up.railway.app
# Health check
curl https://helpful-balance-production-e085.up.railway.app/

# Single image
curl -X POST -F "image=@test.jpg" https://helpful-balance-production-e085.up.railway.app/extract-text

# Batch processing
curl -X POST \
  -F "images=@img1.jpg" \
  -F "images=@img2.png" \
  https://helpful-balance-production-e085.up.railway.app/batch-extract
