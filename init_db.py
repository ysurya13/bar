import sys
import os
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.db.base import Base
from app.db.session import engine
from app.models.extracted_data import ExtractedEntry, BARMetadata, BARNonNeraca, OrganizationPIC, PenyusutanEntry

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")

if __name__ == "__main__":
    init_db()
