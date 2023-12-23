from typing import Union
from fastapi import HTTPException, status, Security, FastAPI, BackgroundTasks
from fastapi.security import APIKeyHeader, APIKeyQuery
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from utilities.callback import handleCallback

load_dotenv()

app = FastAPI()

apiKeys = [os.environ.get("API_KEY")]

api_key_query = APIKeyQuery(name="api-key", auto_error=False)
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


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


class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None


class Resource(BaseModel):
    url: str


@app.get("/")
def read_root():
    return {"Healthy": True}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {"item_name": item.name, "item_id": item_id}


@app.post("/ocr")
def read_item(resource: Resource, background_tasks: BackgroundTasks, api_key: str = Security(get_api_key)):
    background_tasks.add_task(handleCallback, resource.url)
    return {"status": f"processing: {resource.url}"}
