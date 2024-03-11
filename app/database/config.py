# app/config.py

import os

from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    db_url: str = 'postgresql://branfordharris@localhost:9069/receipt-scans'


settings = Settings()