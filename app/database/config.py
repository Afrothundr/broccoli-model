from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field
import os

load_dotenv()


class Settings(BaseSettings):
    db_url: str
    gcp_creds: str = Field(..., env='GCP_CREDS')


settings = Settings(db_url=os.environ.get('DATABASE_URL'))
