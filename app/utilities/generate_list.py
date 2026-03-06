import os
from enum import Enum
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


def build_category_enum(item_types: list[dict]) -> type:
    """Dynamically build a Category enum from the ItemType names fetched from the core DB."""
    members = {
        row["name"].upper().replace(" ", "_").replace("-", "_"): row["name"]
        for row in item_types
    }
    members["UNKNOWN"] = "Unknown"
    return Enum("Category", members)


def build_result_schema(item_types: list[dict]) -> type:
    """Build a dynamic ScrapedItem + Result schema with the live Category enum."""
    Category = build_category_enum(item_types)

    class DynamicScrapedItem(BaseModel):
        name: str
        price: str
        category: Category  # type: ignore[valid-type]

    class DynamicResult(BaseModel):
        store: str
        items: list[DynamicScrapedItem]

    DynamicScrapedItem.__name__ = "ScrapedItem"
    DynamicResult.__name__ = "Result"

    return DynamicResult


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
        result_schema = build_result_schema(item_types)

        prompt = f"""
            Given this OCR result from this image, give me a list of all of the grocery items in this receipt with categories and prices. An example price looks like $12.98.

            When assigning a category to each item, you MUST use one of the following known item types. Match each grocery item to the closest one. If nothing fits, use "Unknown":
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
                "response_schema": result_schema,
            },
        )
        return response.text or ""
    except Exception as e:
        print(e)
        raise
