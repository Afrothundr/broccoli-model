import json
import os
from typing import Any, Optional
from urllib.request import Request, urlopen

from google import genai
from google.genai import types
from PIL import Image
from pydantic import BaseModel
from rapidfuzz import fuzz, process


class ScrapedItem(BaseModel):
    name: str
    price: str
    category: str


class Result(BaseModel):
    store: str
    items: list[ScrapedItem]


def snap_categories(result_json: str, item_types: list[dict]) -> str:
    """Fuzzy-snap Gemini's returned category string to the closest broad ItemType category.

    Gemini is prompted to return one of the broad category values (e.g. "Dairy",
    "Frozen", "Vegetables"). This step tolerates minor wording differences and typos
    by fuzzy-matching against the distinct category values in the ItemType table.
    If no confident match is found we fall back to "Unknown".
    """
    distinct_categories = sorted({row["category"] for row in item_types})

    data = json.loads(result_json)
    for item in data.get("items", []):
        raw = item.get("category", "")
        match = process.extractOne(raw, distinct_categories, scorer=fuzz.WRatio)
        if match and match[1] >= 70:
            item["category"] = match[0]
        else:
            item["category"] = "Unknown"

    return json.dumps(data)


def build_item_type_context(item_types: list[dict]) -> str:
    """Format the distinct broad categories into a context block for the Gemini prompt.

    We ask Gemini to return a broad category (Dairy, Frozen, Vegetables, …) rather
    than a specific ItemType name. Broad categories are far fewer and more reliably
    matched; we then snap to the specific ItemType in post-processing.
    """
    distinct_categories = sorted({row["category"] for row in item_types})
    lines = [f"- {cat}" for cat in distinct_categories]
    return "\n".join(lines)


async def generate_list(
    url: str, ocr: str, item_types: list[dict], jpeg_list: Optional[list[bytes]] = None
) -> str:
    try:
        client = genai.Client(api_key=os.environ.get("AI_KEY"))
        item_type_context = build_item_type_context(item_types)

        prompt = f"""
            Given this OCR result from this image, give me a list of all of the grocery items in this receipt with categories and prices. An example price looks like $12.98.

            When assigning a category to each item, you MUST use one of the following broad category values as the "category" field value. Match each grocery item to the closest one. If nothing fits, use "Unknown":
            {item_type_context}

            OCR: {ocr}
        """

        contents: list[Any] = []
        if jpeg_list is None:
            request_image = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            image = Image.open(urlopen(request_image))
            contents = [image, prompt]
        else:
            contents = [
                types.Part.from_bytes(data=jpeg, mime_type="image/jpeg")
                for jpeg in jpeg_list
            ]
            contents.append(types.Part.from_text(text=prompt))

        response = client.models.generate_content(  # type: ignore[arg-type]
            model="gemini-2.0-flash",
            contents=contents,
            config={
                "response_mime_type": "application/json",
                "response_schema": Result,
            },
        )
        raw_json = response.text or ""
        return snap_categories(raw_json, item_types)
    except Exception as e:
        print(e)
        raise
