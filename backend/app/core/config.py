import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Excel Data Ingestion Engine"
    # Default to SQLite for development, can be overridden by env var
    # On Streamlit Cloud, users can set DATABASE_URL in Secrets
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_PxCai4QS1hYK@ep-shy-hat-a1y4zf7v-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")

    class Config:
        case_sensitive = True

settings = Settings()
