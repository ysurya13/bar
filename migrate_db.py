import sqlite3
import os

# Determine project root and db path
base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "sql_app.db")

def migrate():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Adding column 'catatan_kualitatif' to 'bar_metadata'...")
        cursor.execute("ALTER TABLE bar_metadata ADD COLUMN catatan_kualitatif TEXT")
        conn.commit()
        print("Migration successful.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column 'catatan_kualitatif' already exists.")
        else:
            print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
