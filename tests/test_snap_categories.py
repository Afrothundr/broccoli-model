"""Regression tests for snap_categories (broccoli-model-2kw).

The cottage cheese bug: WRatio's partial matching let brand-noise names clear
the 85 threshold against the wrong specific ItemType, silently swapping a
2-week shelf life for a 6-month one. These tests pin the token_set_ratio
behavior and the tie-as-ambiguity guard.

Run: python -m pytest tests/ (pytest is not in requirements.txt; install ad hoc
or run the module directly — the bottom of this file makes it self-executing).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.utilities.generate_list import snap_categories

# A representative slice of the real catalog: the cheese cluster whose shelf
# lives differ by months, plus unambiguous names.
ITEM_TYPES = [
    {"name": "Cheese (hard such as cheddar, swiss, block parmesan)", "category": "Dairy Products & Eggs"},
    {"name": "Cheese (parmesan; shredded or grated)", "category": "Dairy Products & Eggs"},
    {"name": "Cheese (shredded; cheddar, mozzarella, etc.)", "category": "Dairy Products & Eggs"},
    {"name": "Cheese (soft such as brie, bel paese, goat)", "category": "Dairy Products & Eggs"},
    {"name": "Cottage cheese", "category": "Dairy Products & Eggs"},
    {"name": "Cream cheese", "category": "Dairy Products & Eggs"},
    {"name": "String Cheese", "category": "Dairy Products & Eggs"},
    {"name": "Milk", "category": "Dairy Products & Eggs"},
    {"name": "Yogurt", "category": "Dairy Products & Eggs"},
    {"name": "Bananas", "category": "Produce"},
]


def snap_one(raw_category: str) -> str:
    payload = json.dumps({"items": [{"name": "x", "price": "$1", "category": raw_category}]})
    result = json.loads(snap_categories(payload, ITEM_TYPES))
    return result["items"][0]["category"]


def test_exact_name_still_snaps():
    assert snap_one("Cottage cheese") == "Cottage cheese"


def test_brand_noise_snaps_to_the_right_specific_type():
    # The original bug: WRatio sent this to "Cheese (hard ...)" at 86.
    assert snap_one("Daisy Cottage Cheese 24oz") == "Cottage cheese"


def test_more_brand_noise_cases():
    assert snap_one("GV String Cheese 12ct") == "String Cheese"
    assert snap_one("shredded mozzarella") == "Cheese (shredded; cheddar, mozzarella, etc.)"


def test_bare_generic_token_is_ambiguous_not_a_coin_flip():
    # "Cheese" ties at 100 against every cheese variant — shelf lives that
    # differ by months. It must never pick a specific type. It also shares no
    # tokens with any broad category name, so it lands on Unknown, which the
    # api resolves with a per-item LLM estimate from the full receipt name —
    # a far better failure mode than a coin-flip between 2 weeks and 6 months.
    assert snap_one("Cheese") == "Unknown"


def test_broad_category_fallback_still_works():
    # Gemini ignoring instructions and returning a generic label should land
    # in the matching broad bucket, not Unknown.
    assert snap_one("Dairy") == "Dairy Products & Eggs"
    assert snap_one("produce") == "Produce"


def test_unrelated_input_falls_to_unknown():
    assert snap_one("motor oil 5w30") == "Unknown"


def test_unambiguous_short_names_unaffected():
    assert snap_one("Milk") == "Milk"
    assert snap_one("bananas") == "Bananas"


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except AssertionError as err:
                failures += 1
                print(f"FAIL {name}: {err}")
    sys.exit(1 if failures else 0)
