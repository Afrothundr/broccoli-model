from dotenv import load_dotenv

from pydantic import BaseSettings, Field

load_dotenv()


class Settings(BaseSettings):
    db_url: str = Field(..., env='DATABASE_URL')
    gcp_creds: str = Field(..., env='GCP_CREDS')


settings = Settings()
