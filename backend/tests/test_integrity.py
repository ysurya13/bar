import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.db.session import SessionLocal, engine
from sqlalchemy import text

def test_integrity():
    print("Testing Database Integrity...")
    db = SessionLocal()
    try:
        # 1. Test basic connectivity
        result = db.execute(text("SELECT version();")).fetchone()
        print(f"Connected to: {result[0]}")

        # 2. Test table existence
        tables = ["bar_metadata", "extracted_entries", "ref_accounts", "ref_organizations", "ref_staff"]
        for table in tables:
            res = db.execute(text(f"SELECT count(*) FROM {table}")).fetchone()
            print(f"Table '{table}' exists and has {res[0]} rows.")

        print("\nIntegrity tests passed successfully.")
    except Exception as e:
        print(f"Integrity test FAILED: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    test_integrity()
