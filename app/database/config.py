from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field
import os

load_dotenv()


class Settings(BaseSettings):
    db_url: str = Field(..., alias='DATABASE_URL')
    gcp_creds: str = Field(..., alias='GCP_CREDS')

    class Config:
        env_file = '.env'
        populate_by_name = True


settings = Settings()
