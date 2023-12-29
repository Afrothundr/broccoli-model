import os

from pydantic import BaseModel
from utilities.ocr import ocrUrl
import requests

class ScrapedItem(BaseModel):
  name: str


def handleCallback(url: str, receiptId: int):
    print(f"processing: {url}")
    list = ocrUrl(url)
    data = []
    for result in list:
        try:
            float(result)
            continue
        except ValueError:
            if "$" in result:
                continue
            else:
                data.append(ScrapedItem(name=result).model_dump())
    requests.post(f'{os.environ.get("SCHEDULER_API_URL")}/receipts/callback', json={
        "data": data,
        "receiptId": receiptId
    }, headers={"x-api-key": os.environ.get("SCHEDULER_API_KEY")})