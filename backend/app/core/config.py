import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Excel Data Ingestion Engine"
    # Default to SQLite for development, can be overridden by env var
    # On Streamlit Cloud, users can set DATABASE_URL in Secrets
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")

    class Config:
        case_sensitive = True

settings = Settings()
