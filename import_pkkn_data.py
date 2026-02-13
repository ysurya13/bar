import sys
import os
import pandas as pd

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.db.session import SessionLocal
from app.models.extracted_data import OrganizationPIC

def import_pkkn_data():
    """Import PKKN counterpart officer data from Excel files."""
    
    # Load the Excel files
    df_pkkn = pd.read_excel("referensi/referensi_penandatangan_pkkn.xlsx")
    df_pic_kl = pd.read_excel("referensi/referensi_pic_kl.xlsx")
    
    print(f"Loaded {len(df_pkkn)} PKKN officers")
    print(f"Loaded {len(df_pic_kl)} organization assignments")
    
    # Merge to get kode_ba with their assigned PKKN officer
    # df_pic_kl has: kode_ba, pic_seksi, direktorat, seksi, id_direktorat
    # df_pkkn has: id_subdirektorat, nama, jabatan, nip
    
    # The id_direktorat in df_pic_kl maps to id_subdirektorat in df_pkkn
    merged = df_pic_kl.merge(
        df_pkkn,
        left_on='id_direktorat',
        right_on='id_subdirektorat',
        how='left'
    )
    
    print(f"\nMerged {len(merged)} organization-officer assignments")
    print("\nSample data:")
    print(merged[['kode_ba', 'nama', 'nip', 'jabatan']].head())
    
    # Import to database
    db = SessionLocal()
    try:
        # Clear existing data
        deleted_count = db.query(OrganizationPIC).delete()
        print(f"\nCleared {deleted_count} existing records")
        
        # Insert new data
        inserted_count = 0
        for _, row in merged.iterrows():
            if pd.notna(row['nama']) and pd.notna(row['kode_ba']):
                pic = OrganizationPIC(
                    kode_ba=str(int(row['kode_ba'])).zfill(3),  # Format as 3-digit string
                    nama_pic=row['nama'],
                    nip_pic=str(int(row['nip'])) if pd.notna(row['nip']) else None,
                    jabatan_pic=row['jabatan']
                )
                db.add(pic)
                inserted_count += 1
        
        db.commit()
        print(f"Successfully imported {inserted_count} PKKN counterpart officers")
        
        # Verify
        print("\nVerification - sample records:")
        samples = db.query(OrganizationPIC).limit(5).all()
        for s in samples:
            print(f"  BA {s.kode_ba}: {s.nama_pic} ({s.jabatan_pic})")
            
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import_pkkn_data()
