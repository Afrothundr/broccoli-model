import os

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    db_url: str = Field(..., alias="DATABASE_URL")
    core_db_url: str = Field(..., alias="CORE_DATABASE_URL")
    gcp_creds: str = Field(..., alias="GCP_CREDS")

    class Config:
        env_file = ".env"
        populate_by_name = True


settings = Settings()
