from fastapi import HTTPException, status, Security, FastAPI
from fastapi.security import APIKeyHeader, APIKeyQuery
from fastapi.middleware.cors import CORSMiddleware
from app.database.db import database, Receipt
from pydantic import BaseModel
import os
import spacy
from dotenv import load_dotenv
from contextlib import asynccontextmanager

from app.utilities.ocr import ocrUrl


load_dotenv()

ml_models = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    ml_models['np'] = spacy.load("en_receipt_model")
    if not database.is_connected:
        await database.connect()

    yield

    if database.is_connected:
        await database.disconnect()

    # Clean up the ML models and release the resources
    ml_models.clear()

app = FastAPI(lifespan=lifespan)

apiKeys = [os.environ.get("API_KEY")]

api_key_query = APIKeyQuery(name="api-key", auto_error=False)
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

origins = [
    "http://localhost:5007",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_api_key(
    api_key_query: str = Security(api_key_query),
    api_key_header: str = Security(api_key_header),
) -> str:
    if api_key_query in apiKeys:
        return api_key_query
    if api_key_header in apiKeys:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )


class Resource(BaseModel):
    url: str
    receiptId: int


class ScrapedItem(BaseModel):
    name: str
    price: str


@app.get("/")
def read_root():
    return {"Healthy": True }


@app.post("/ocr")
async def read_item(resource: Resource, api_key: str = Security(get_api_key)):
    text = ocrUrl(resource.url)
    await Receipt.objects.get_or_create(text=text)
    doc = ml_models['np'](text)
    data = []
    try:
        for index, ent in enumerate(doc.ents):
            if ent.label_ == 'FOOD':
                price = '0.00'
                for next_ent in doc.ents[index:]:
                    if next_ent.label_ == 'PRICE':
                        price = next_ent.text
                        break
                try:
                    item = ScrapedItem(name=ent.text.title(),
                                price=float(price))
                    
                    data.append(dict(item))
                except:
                    continue
        return {"data": data, "receiptId": resource.receiptId}
    except:
        raise HTTPException(
            status_code=500, detail=f'Problem processing image: {resource.url}')