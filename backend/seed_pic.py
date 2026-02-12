import pandas as pd
import sys
import os

# Add backend to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from app.core.config import settings

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
    
    try:
        # Prepare final columns
        df_pic = pd.DataFrame()
        df_pic['kode_ba'] = df_joined['kode_ba'].astype(str).str.zfill(3)
        df_pic['nama_pic'] = df_joined['nama']
        df_pic['nip_pic'] = df_joined['nip'].astype(str)
        df_pic['jabatan_pic'] = df_joined['jabatan']
        
        # Save to CSV
        df_pic.to_csv(settings.PIC_CSV, index=False)
        print(f"Successfully saved {len(df_pic)} PIC records to {settings.PIC_CSV}.")
    except Exception as e:
        print(f"Error seeding PICs: {e}")

if __name__ == "__main__":
    seed_pics()
