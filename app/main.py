from fastapi import HTTPException, status, Security, FastAPI
from fastapi.security import APIKeyHeader, APIKeyQuery
from fastapi.middleware.cors import CORSMiddleware
from app.database.db import database, Receipt
from app.utilities.generate_list import generate_list, ScrapedItem
from pydantic import BaseModel
from pydantic_core import from_json
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager

from app.utilities.ocr import ocrUrl


load_dotenv()

ml_models = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not database.is_connected:
        await database.connect()

    yield

    if database.is_connected:
        await database.disconnect()

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


@app.get("/")
def read_root():
    return {"Healthy": True}


@app.post("/ocr")
async def read_item(resource: Resource, api_key: str = Security(get_api_key)):
    try:
        (text, jpeg_list) = await ocrUrl(resource.url)
        await Receipt.objects.get_or_create(text=text)
        data = None
        if jpeg_list is None:
            data = from_json(await generate_list(resource.url, text))
        else:
            data = from_json(await generate_list(resource.url, text, jpeg_list[0]))
        return {"data": data, "receiptId": resource.receiptId}
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500, detail=f'Problem processing image: {resource.url}')
