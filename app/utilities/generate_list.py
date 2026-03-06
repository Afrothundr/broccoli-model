import os
from typing import Any, Optional
from urllib.request import Request, urlopen

from google import genai
from google.genai import types
from PIL import Image
from pydantic import BaseModel


class ScrapedItem(BaseModel):
    name: str
    price: str
    category: str


class Result(BaseModel):
    store: str
    items: list[ScrapedItem]


def build_item_type_context(item_types: list[dict]) -> str:
    """Format item types into a readable context block for the Gemini prompt."""
    lines = []
    for row in item_types:
        lines.append(f"- {row['name']} (category: {row['category']})")
    return "\n".join(lines)


async def generate_list(
    url: str, ocr: str, item_types: list[dict], jpeg_list: Optional[list[bytes]] = None
) -> str:
    try:
        client = genai.Client(api_key=os.environ.get("AI_KEY"))
        item_type_context = build_item_type_context(item_types)

        prompt = f"""
            Given this OCR result from this image, give me a list of all of the grocery items in this receipt with categories and prices. An example price looks like $12.98.

            When assigning a category to each item, you MUST use one of the following known item types as the "category" field value. Match each grocery item to the closest one. If nothing fits, use "Unknown":
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
        return response.text or ""
    except Exception as e:
        print(e)
        raise
