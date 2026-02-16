import sys
import os

# Add backend to path (backend/app/db/init_db.py -> backend)
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import engine
from app.db.base import Base
# Import models to ensure they are registered with Base
from app.models.reference import ReferenceAccount, ReferenceOrganization, ReferenceStaff
from app.models.extracted_data import ExtractedEntry

import time

def init_db():
    print("Initializing Database...")
    max_retries = 3
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            Base.metadata.create_all(bind=engine)
            print("Database initialized successfully.")
            return
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Database initialization failed.")
                raise e

if __name__ == "__main__":
    init_db()
