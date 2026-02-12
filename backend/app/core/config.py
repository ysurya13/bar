import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Excel Data Ingestion Engine"
    # Default to SQLite for development, can be overridden by env var
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Fallback for Streamlit Secrets if no env var is set
        if self.DATABASE_URL == "sqlite:///./sql_app.db":
            try:
                import streamlit as st
                if "DATABASE_URL" in st.secrets:
                    self.DATABASE_URL = st.secrets["DATABASE_URL"]
            except Exception:
                # Streamlit not available or secrets not configured
                pass

    class Config:
        case_sensitive = True

settings = Settings()
