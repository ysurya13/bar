"""
Comprehensive script to import all reference data from Excel files to PostgreSQL database.

This script imports:
1. PKKN Counterpart Officers (for the "Generate BAR" page)
2. Reference Accounts
3. Reference Organizations
"""
import sys
import os
import pandas as pd

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.db.session import SessionLocal
from app.models.extracted_data import OrganizationPIC
from app.models.reference import ReferenceAccount, ReferenceOrganization

def import_pkkn_counterparts():
    """Import PKKN counterpart officer data."""
    print("=" * 60)
    print("IMPORTING PKKN COUNTERPART OFFICERS")
    print("=" * 60)
    
    # Load the Excel files
    df_pkkn = pd.read_excel("referensi/referensi_penandatangan_pkkn.xlsx")
    df_pic_kl = pd.read_excel("referensi/referensi_pic_kl.xlsx")
    
    print(f"Loaded {len(df_pkkn)} PKKN officers")
    print(f"Loaded {len(df_pic_kl)} organization assignments")
    
    # Merge to get kode_ba with their assigned PKKN officer
    merged = df_pic_kl.merge(
        df_pkkn,
        left_on='id_direktorat',
        right_on='id_subdirektorat',
        how='left'
    )
    
    print(f"Merged {len(merged)} organization-officer assignments")
    
    # Import to database
    db = SessionLocal()
    try:
        # Clear existing data
        deleted_count = db.query(OrganizationPIC).delete()
        print(f"Cleared {deleted_count} existing records")
        
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
        print(f"✓ Successfully imported {inserted_count} PKKN counterpart officers")
        
        # Verify
        print("\nSample records:")
        samples = db.query(OrganizationPIC).limit(5).all()
        for s in samples:
            print(f"  BA {s.kode_ba}: {s.nama_pic}")
            
    except Exception as e:
        db.rollback()
        print(f"✗ Error: {e}")
        raise
    finally:
        db.close()

def import_reference_accounts():
    """Import reference accounts."""
    print("\n" + "=" * 60)
    print("IMPORTING REFERENCE ACCOUNTS")
    print("=" * 60)
    
    df_akun = pd.read_excel("referensi/referensi_akun.xlsx")
    print(f"Loaded {len(df_akun)} reference accounts")
    
    db = SessionLocal()
    try:
        # Clear existing data
        deleted_count = db.query(ReferenceAccount).delete()
        print(f"Cleared {deleted_count} existing records")
        
        # Insert new data
        inserted_count = 0
        for _, row in df_akun.iterrows():
            if pd.notna(row['kode_akun']):
                account = ReferenceAccount(
                    kode_akun=str(int(row['kode_akun'])),
                    uraian_akun=row['uraian'] if pd.notna(row['uraian']) else '',
                    kategori=row.get('akun_umum', '')
                )
                db.add(account)
                inserted_count += 1
        
        db.commit()
        print(f"✓ Successfully imported {inserted_count} reference accounts")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error: {e}")
        raise
    finally:
        db.close()

def import_reference_organizations():
    """Import reference organizations."""
    print("\n" + "=" * 60)
    print("IMPORTING REFERENCE ORGANIZATIONS")
    print("=" * 60)
    
    df_kl = pd.read_excel("referensi/referensi_kl.xlsx")
    print(f"Loaded {len(df_kl)} reference organizations")
    
    # Check what columns are in the file
    print(f"Columns: {df_kl.columns.tolist()}")
    
    db = SessionLocal()
    try:
        # Clear existing data
        deleted_count = db.query(ReferenceOrganization).delete()
        print(f"Cleared {deleted_count} existing records")
        
        # Insert new data
        # Assuming the file has columns like 'kode_ba' and 'uraian_ba' or similar
        inserted_count = 0
        for _, row in df_kl.iterrows():
            # Try to find the kode_ba column (might be named differently)
            kode_col = None
            uraian_col = None
            
            for col in df_kl.columns:
                col_lower = str(col).lower()
                if 'kode' in col_lower and 'ba' in col_lower:
                    kode_col = col
                elif 'uraian' in col_lower or 'nama' in col_lower:
                    uraian_col = col
            
            if kode_col and uraian_col:
                if pd.notna(row[kode_col]):
                    org = ReferenceOrganization(
                        kode_ba=str(int(row[kode_col])).zfill(3),
                        uraian_ba=row[uraian_col] if pd.notna(row[uraian_col]) else ''
                    )
                    db.add(org)
                    inserted_count += 1
        
        db.commit()
        print(f"✓ Successfully imported {inserted_count} reference organizations")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error: {e}")
        raise
    finally:
        db.close()

def main():
    """Main function to import all reference data."""
    print("\n" + "=" * 60)
    print("  IMPORTING ALL REFERENCE DATA TO POSTGRESQL")
    print("=" * 60 + "\n")
    
    try:
        import_pkkn_counterparts()
        import_reference_accounts()
        import_reference_organizations()
        
        print("\n" + "=" * 60)
        print("✓ ALL IMPORTS COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ IMPORT FAILED: {e}")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
