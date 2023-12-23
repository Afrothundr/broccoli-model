from utilities.ocr import ocrUrl


def handleCallback(url: str):
    print(f"processing: {url}")
    list = ocrUrl(url)
    print(list)