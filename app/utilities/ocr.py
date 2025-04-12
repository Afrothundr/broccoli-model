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
    try:
        r = requests.get(url)
        content_type = r.headers.get('content-type')
        result = str
        jpeg_bytes_list = None
        if content_type == 'application/pdf':
            # Convert PDF pages to JPEG
            jpeg_bytes_list = convert_pdf_pages_to_jpegs(
                url,
                start_page=0,
                end_page=5
            )

            # Process pages concurrently
            tasks = [process_page(jpeg_bytes)
                     for jpeg_bytes in jpeg_bytes_list]
            results = await asyncio.gather(*tasks)

            # Combine results with page numbers
            formatted_results = []
            for i, text in enumerate(results, 1):
                if text.strip():  # Only include non-empty pages
                    formatted_results.append(text)

            result = ' '.join(formatted_results)
        else:
            # Handle non-PDF files as before
            image = vision.Image()
            image.source.image_uri = url

            response = client.text_detection(image=image)
            if response.error.message:
                raise Exception("errors", response.error.message)
            texts = response.text_annotations
            result = texts[0].description if texts else ""
    except Exception as e:
        print(e)
    return result.replace('\n', ' '), jpeg_bytes_list
