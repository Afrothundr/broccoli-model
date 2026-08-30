import mimetypes
import json
import os
from app.database.config import settings
from google.cloud import vision
import requests
import pymupdf
from io import BytesIO
import asyncio

if os.path.exists('credentials.json'):
    pass
else:
    with open('credentials.json', 'w') as credFile:
        json.dump(json.loads(settings.gcp_creds), credFile)

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'credentials.json'
client = vision.ImageAnnotatorClient()


def convert_pdf_pages_to_jpegs(pdf_url: str, start_page: int = 0, end_page: int = None):
    # Download PDF
    response = requests.get(pdf_url)
    if response.status_code != 200:
        raise Exception(f"Failed to download PDF: {response.status_code}")

    # Load PDF from memory
    pdf_stream = BytesIO(response.content)
    doc = pymupdf.open(stream=pdf_stream, filetype="pdf")

    if doc.page_count == 0:
        raise Exception("PDF has no pages")

    # Validate page range
    end_page = min(end_page or doc.page_count, doc.page_count)
    start_page = max(0, min(start_page, end_page - 1))

    jpeg_bytes_list = []

    try:
        # Convert each page
        for page_num in range(start_page, end_page):
            page = doc[page_num]
            # Convert to image with higher resolution
            # 2x zoom for better quality
            pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
            jpeg_bytes_list.append(pix.tobytes("jpeg"))

    finally:
        # Clean up
        doc.close()

    return jpeg_bytes_list


async def process_page(jpeg_bytes: bytes):
    """Process a single page with OCR"""
    image = vision.Image(content=jpeg_bytes)
    response = client.text_detection(image=image)

    if response.error.message:
        raise Exception(f"OCR error: {response.error.message}")

    texts = response.text_annotations
    if not texts:
        return ""

    # First annotation contains all text
    return texts[0].description if texts else ""


async def ocrUrl(url: str):
    """Download the receipt ourselves and OCR the bytes.

    GCV's image_uri mode makes GOOGLE fetch the URL server-side, and that
    fetcher fails ("URL does not appear to be accessible by us") on plenty of
    public hosts — which used to surface as a confusing 500 (the old error
    path also swallowed the real exception and crashed on `result.replace`).
    Downloading here and passing `content=` removes that whole failure class;
    the PDF path already worked this way.
    """
    jpeg_bytes_list = None
    # A UA is required by several hosts (Wikimedia 403s the default
    # python-requests agent) — same header the Gemini image fetch uses.
    r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    if r.status_code != 200:
        raise Exception(f"Failed to download receipt image: {r.status_code}")
    content_type = r.headers.get('content-type', '')

    if content_type == 'application/pdf':
        # Convert PDF pages to JPEG
        jpeg_bytes_list = convert_pdf_pages_to_jpegs(
            url,
            start_page=0,
            end_page=5
        )

        # Process pages concurrently
        results = await asyncio.gather(
            *(process_page(jpeg_bytes) for jpeg_bytes in jpeg_bytes_list)
        )

        # Combine results with page numbers
        result = ' '.join(text for text in results if text.strip())
    else:
        # Handle non-PDF files as image bytes
        image = vision.Image(content=r.content)
        response = client.text_detection(image=image)
        if response.error.message:
            raise Exception(f"OCR error: {response.error.message}")
        texts = response.text_annotations
        result = texts[0].description if texts else ""

    return result.replace('\n', ' '), jpeg_bytes_list
