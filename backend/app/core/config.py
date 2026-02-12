import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Excel Data Ingestion Engine"
    
    # CSV Storage Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    
    ENTRIES_CSV: str = os.path.join(DATA_DIR, "extracted_entries.csv")
    METADATA_CSV: str = os.path.join(DATA_DIR, "bar_metadata.csv")
    NON_NERACA_CSV: str = os.path.join(DATA_DIR, "bar_non_neraca.csv")
    PIC_CSV: str = os.path.join(DATA_DIR, "organization_pics.csv")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure data directory exists
        if not os.path.exists(self.DATA_DIR):
            os.makedirs(self.DATA_DIR, exist_ok=True)

    class Config:
        case_sensitive = True

settings = Settings()
