import os

from dotenv import load_dotenv

load_dotenv()
from fastapi import FastAPI, HTTPException, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader, APIKeyQuery
from pydantic import BaseModel
from pydantic_core import from_json

from app.utilities.generate_list import generate_list
from app.utilities.ocr import ocrUrl

app = FastAPI()

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


class ItemType(BaseModel):
    name: str
    category: str


class Resource(BaseModel):
    url: str
    # Optional: broccoli-model is stateless and only echoes this back. The
    # caller (broccoli-api) already holds the receipt id (a cuid string) in its
    # own context, so it doesn't need to send one. Kept for backward compat.
    receiptId: str | None = None
    itemTypes: list[ItemType]


@app.get("/")
def read_root():
    return {"Healthy": True}


@app.post("/ocr")
async def read_item(resource: Resource, api_key: str = Security(get_api_key)):
    try:
        (text, jpeg_list) = await ocrUrl(resource.url)
        item_types = [item_type.model_dump() for item_type in resource.itemTypes]
        data = None
        if jpeg_list is None:
            data = from_json(await generate_list(resource.url, text, item_types))
        else:
            data = from_json(
                await generate_list(resource.url, text, item_types, jpeg_list)
            )
        return {"data": data, "receiptId": resource.receiptId}
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500, detail=f"Problem processing image: {resource.url}"
        )
