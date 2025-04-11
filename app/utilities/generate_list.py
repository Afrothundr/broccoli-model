from PIL import Image
from google import genai
import os
import enum
from urllib.request import urlopen, Request
from pydantic import BaseModel
from io import BytesIO

client = genai.Client(api_key=os.environ.get("AI_KEY"))


class Category(enum.Enum):
    APPLES = 'Apples'
    APRICOTS = 'Apricots'
    ARTICHOKES = 'Artichokes'
    ARUGULA = 'Arugula'
    ASPARAGUS = 'Asparagus'
    AVOCADOS = 'Avocados'
    BACON = 'Bacon'
    BANANAS = 'Bananas'
    BASIL = 'Basil'
    BEET = 'Beet'
    BEETS = 'Beets'
    BOK_CHOY = 'Bok Choy'
    BREAD = 'Bread'
    BROCCOLI = 'Broccoli'
    BRUSSELS_SPROUTS = 'Brussels sprouts'
    BUTTER = 'Butter'
    CABBAGE = 'Cabbage'
    CARROTS = 'Carrots'
    CAULIFLOWER = 'Cauliflower'
    CELERY = 'Celery'
    CHARD = 'Chard'
    CHEESE = 'Cheese'
    CHERRIES = 'Cherries'
    CILANTRO = 'Cilantro'
    CITRUS = 'Citrus'
    COCONUT_MILK = 'Coconut Milk'
    COLLARD_GREENS = 'Collard Greens'
    CORN_ON_THE_COB = 'Corn on the cob'
    COTTAGE_CHEESE = 'Cottage Cheese'
    CUCUMBERS = 'Cucumbers'
    CUT_MELONS = 'Cut Melons'
    DELI_MEAT = 'Deli meat'
    DILL = 'Dill'
    EGGPLANT = 'Eggplant'
    EGGS = 'Eggs'
    ENDIVE = 'Endive'
    FIGS = 'Figs'
    FLOUR = 'Flour'
    FRESH_MEAT = 'Fresh meat'
    FRESH_PEAS = 'Fresh Peas'
    FROZEN_FOOD = 'Frozen food'
    FROZEN_SHELLFISH = 'Frozen shellfish'
    GARLIC = 'Garlic'
    GINGER = 'Ginger'
    GRAPEFRUIT = 'Grapefruit'
    GRAPES = 'Grapes'
    GREEN_BEANS = 'Green Beans'
    GREEN_ONIONS = 'Green Onions'
    HARD_CHEESE = 'Hard Cheese'
    HOT_DOGS_OR_PRECOOKED_SAUSAGE = 'Hot dogs or precooked sausage'
    KALE = 'Kale'
    KIWI = 'Kiwi'
    LAVENDER = 'Lavender'
    LEMON = 'Lemon'
    LETTUCE = 'Lettuce'
    LIME = 'Lime'
    MANGO = 'Mango'
    MANGOES = 'Mangoes'
    MILK = 'Milk'
    MINT = 'Mint'
    MUSHROOM = 'Mushroom'
    MUSHROOMS = 'Mushrooms'
    NECTARINE = 'Nectarine'
    NECTARINES = 'Nectarines'
    NON_PERISHABLE = 'Non-perishable'
    OAT_MILK = 'Oat Milk'
    OATS = 'Oats'
    ONION = 'Onion'
    ONIONS = 'Onions'
    ORANGE = 'Orange'
    PAPAYA = 'Papaya'
    PAPAYAS = 'Papayas'
    PARSLEY = 'Parsley'
    PARSNIPS = 'Parsnips'
    PASSION_FRUIT = 'Passion Fruit'
    PASTA = 'Pasta'
    PEACH = 'Peach'
    PEACHES = 'Peaches'
    PEARS = 'Pears'
    PEPPERS = 'Peppers'
    PINEAPPLE = 'Pineapple'
    PINEAPPLES = 'Pineapples'
    PLUM = 'Plum'
    PLUMS = 'Plums'
    POMEGRANATE = 'Pomegranate'
    POTATOES = 'Potatoes'
    QUINOA = 'Quinoa'
    RADICCHIO = 'Radicchio'
    RADISHES = 'Radishes'
    RICE = 'Rice'
    ROSEMARY = 'Rosemary'
    SAGE = 'Sage'
    SELF_DESTRUCTING_SPINACH = 'Self Destructing Spinach'
    SHALLOTS = 'Shallots'
    SNAP_PEAS = 'Snap Peas'
    SOFT_CHEESE = 'Soft Cheese'
    SPINACH = 'Spinach'
    SQUASH = 'Squash'
    SUGAR = 'Sugar'
    SWEET_POTATOES = 'Sweet Potatoes'
    THYME = 'Thyme'
    TOFU = 'Tofu'
    TOMATOES = 'Tomatoes'
    TURNIPS = 'Turnips'
    UNKNOWN = 'Unknown'
    WHOLE_GRAINS = 'Whole grains'
    WHOLE_MELONS = 'Whole Melons'
    YOGURT = 'Yogurt'
    ZUCCHINI = 'Zucchini'


class ScrapedItem(BaseModel):
    name: str
    price: str
    category: Category


async def generate_list(url: str, ocr: str, jpeg: bytes):
    try:
        request_image = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        image = None
        if jpeg is None:
            image = Image.open(urlopen(request_image))
        else:
            image = Image.open(BytesIO(jpeg))
        prompt = f"""
            Given this OCR result from this image, give me a list of all of the grocery items in this receipt with categories and prices. An example price looks like $12.98
            OCR: {ocr}
        """
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[image, prompt],
            config={
                'response_mime_type': "application/json", "response_schema": list[ScrapedItem]
            },
        )
        return response.text
    except Exception as e:
        print(e)
