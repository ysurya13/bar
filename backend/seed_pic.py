import pandas as pd
import sys
import os

# Add backend to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from app.db.session import SessionLocal
from app.models.extracted_data import OrganizationPIC

def seed_pics():
    # Detect project root (parent of backend folder)
    backend_root = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(backend_root)
    
    mapping_path = os.path.join(project_root, "referensi", "referensi_pic_kl.xlsx")
    officer_path = os.path.join(project_root, "referensi", "referensi_penandatangan_pkkn.xlsx")
    
    if not os.path.exists(mapping_path) or not os.path.exists(officer_path):
        print(f"Reference files not found.")
        return

    df_map = pd.read_excel(mapping_path)
    df_off = pd.read_excel(officer_path)
    
    # Merge on id_direktorat (from df_map) and id_subdirektorat (from df_off)
    df_joined = pd.merge(
        df_map, 
        df_off, 
        left_on='id_direktorat', 
        right_on='id_subdirektorat', 
        how='inner'
    )
    
    db = SessionLocal()
    try:
        db.query(OrganizationPIC).delete()
        
        for _, row in df_joined.iterrows():
            pic = OrganizationPIC(
                kode_ba=str(row['kode_ba']).zfill(3),
                nama_pic=row['nama'],
                nip_pic=str(row['nip']),
                jabatan_pic=row['jabatan']
            )
            db.add(pic)
        
        db.commit()
        print(f"Successfully seeded {len(df_joined)} PIC records.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding PICs: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_pics()
