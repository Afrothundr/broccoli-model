import json
import os
from typing import Any, Optional
from urllib.request import Request, urlopen

from google import genai
from google.genai import types
from PIL import Image
from pydantic import BaseModel
from rapidfuzz import fuzz, process, utils


class ScrapedItem(BaseModel):
    name: str
    price: str
    category: str
    # Gemini's self-assessed extraction confidence, 0.0-1.0. Surfaced to the
    # user as a review chip (amber when low) so they know which lines to
    # double-check. NOTE: must stay required (no default) — the Gemini API
    # rejects response schemas that declare defaults. The prompt instructs
    # the model to always emit it.
    confidence: float


class Result(BaseModel):
    store: str
    date: str
    items: list[ScrapedItem]


def snap_categories(result_json: str, item_types: list[dict]) -> str:
    """Fuzzy-snap Gemini's returned ItemType name to the closest exact name in the DB.

    Gemini is prompted to return one of the 162 specific ItemType names. This step
    tolerates minor wording differences / OCR noise by fuzzy-matching the returned
    string against all known names with a high confidence threshold (85).

    Scored with token_set_ratio, not WRatio. WRatio's partial matching let a
    brand-noise name clear the threshold against the wrong specific type:
    "Daisy Cottage Cheese 24oz" hit "Cheese (hard such as cheddar, swiss,
    block parmesan)" at 86 — a 2-week item stamped with a 6-month shelf life.
    token_set_ratio ignores word order and extra tokens, so the same string
    lands on "Cottage cheese" at 100.

    The trade-off: a bare shared token ("Cheese") now ties at 100 against
    every variant. A tie at the top means the input genuinely doesn't say
    which specific type it is, so ties are treated as no-match and fall
    through to the broad-category pass — never a coin-flip between shelf
    lives that differ by months.

    If the name match is not confident enough we fall back to fuzzy-matching the
    returned string against the broad category values (70 threshold) so the item
    still lands in a sensible bucket rather than "Unknown".
    """
    all_names = [row["name"] for row in item_types]
    distinct_categories = sorted({row["category"] for row in item_types})

    data = json.loads(result_json)
    for item in data.get("items", []):
        raw = item.get("category", "")

        # First try: snap to a specific ItemType name — top two so a tied
        # top score is detectable as ambiguity.
        name_matches = process.extract(
            raw,
            all_names,
            scorer=fuzz.token_set_ratio,
            processor=utils.default_process,
            limit=2,
        )
        if name_matches and name_matches[0][1] >= 85:
            tied = len(name_matches) > 1 and name_matches[1][1] == name_matches[0][1]
            if not tied:
                item["category"] = name_matches[0][0]
                continue

        # Second try: snap to a broad category
        cat_match = process.extractOne(
            raw,
            distinct_categories,
            scorer=fuzz.token_set_ratio,
            processor=utils.default_process,
        )
        if cat_match and cat_match[1] >= 70:
            item["category"] = cat_match[0]
        else:
            item["category"] = "Unknown"

    return json.dumps(data)


def build_item_type_context(item_types: list[dict]) -> str:
    """Format all 162 ItemType names grouped by broad category for the Gemini prompt.

    Grouping by category makes it easier for the model to scan and pick the right
    specific name rather than inventing its own category label.
    """
    by_category: dict[str, list[str]] = {}
    for row in item_types:
        by_category.setdefault(row["category"], []).append(row["name"])

    lines: list[str] = []
    for category in sorted(by_category):
        names = ", ".join(sorted(by_category[category]))
        lines.append(f"{category}: {names}")
    return "\n".join(lines)


async def generate_list(
    url: str, ocr: str, item_types: list[dict], jpeg_list: Optional[list[bytes]] = None
) -> str:
    try:
        client = genai.Client(api_key=os.environ.get("AI_KEY"))
        item_type_context = build_item_type_context(item_types)

        prompt = f"""
            Given this OCR result from this image, give me a list of all of the grocery items in this receipt with categories and prices. An example price looks like $12.98.

            For each item's "category" field you MUST copy one of the exact item type names from the list below — do not invent new names or use generic labels like "Snacks" or "Dairy". Each line below shows a broad group followed by the exact names you may use. Pick the closest match. If nothing fits, use "Unknown".

            For each item also give a "confidence" between 0.0 and 1.0: how sure you are that the name, price, and category were read correctly from the receipt. Be honest — blurry lines, unusual products, or guessed prices get low confidence (below 0.7); crisp printed lines get high confidence (0.85+).

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
            # gemini-2.0-flash was retired by Google (generate_content 404s);
            # 2.5-flash is the current stable flash tier. Model is
            # env-configurable (GEMINI_MODEL) so future swaps/retirements
            # need no code change.
            model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
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
