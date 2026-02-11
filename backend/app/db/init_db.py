import sys
import os

# Add backend to path (backend/app/db/init_db.py -> backend)
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import engine
from app.db.base import Base
# Import models to ensure they are registered with Base
from app.models.reference import ReferenceAccount, ReferenceOrganization, ReferenceStaff
from app.models.extracted_data import ExtractedEntry

def init_db():
    print("Initializing Database...")
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()
