from PIL import Image, ImageDraw
import os

os.makedirs("sample_images", exist_ok=True)

# Create test document
img1 = Image.new('RGB', (800, 600), color='white')
d1 = ImageDraw.Draw(img1)
d1.text((50, 50), "OCR Test Document\n\nThis is a sample document for testing.", fill='black')
img1.save('sample_images/test_document.jpg')

# Create receipt
img2 = Image.new('RGB', (400, 600), color='white')
d2 = ImageDraw.Draw(img2)
d2.text((20, 20), "RECEIPT\nStore Name\n\nItem 1    $10.99\nItem 2    $25.50\n\nTOTAL:    $36.49", fill='black')
img2.save('sample_images/receipt.png')

# Create no-text image
img3 = Image.new('RGB', (400, 300), color='lightblue')
img3.save('sample_images/no_text.jpg')

print("Test images created!")
