from typing import List, BinaryIO
import pandas as pd
from app.services.extraction.base import BaseExtractor

class PenyusutanExtractor(BaseExtractor):
    
    def extract(self, file_content: BinaryIO, filename: str) -> List[dict]:
        df = pd.read_excel(file_content, header=None)
        metadata = self.parse_metadata(df)
        
        # 1. Identify Type (Intra vs Ekstra)
        jenis_penyusutan = "INTRAKOMPTABEL" # Default
        
        # Search first 10 rows for keywords
        found_type = False
        for idx in range(min(10, len(df))):
            row_str = " ".join([str(val).upper() for val in df.iloc[idx].values if pd.notna(val)])
            if "EKSTRAKOMPTABEL" in row_str:
                jenis_penyusutan = "EKSTRAKOMPTABEL"
                found_type = True
                break
            elif "INTRAKOMPTABEL" in row_str:
                jenis_penyusutan = "INTRAKOMPTABEL"
                found_type = True
                break
        
        extracted_data = []
        
        # 2. Iterate and Extract
        # Based on inspection, data row has:
        # Col 0: Kode Akun (6 digits)
        # Col 2: Uraian
        # Col 6: Nilai Perolehan
        # Col 7: Saldo Awal
        # Col 8: Mutasi Tambah
        # Col 9: Mutasi Kurang
        # Col 12: Saldo Akhir
        # Last Col: Nilai Buku
        
        for index, row in df.iterrows():
            try:
                # Filter by Code (Col 0)
                code_raw = row[0]
                if pd.isna(code_raw):
                    continue
                
                code_str = str(code_raw).strip()
                
                # STRICT FILTER: Must be exactly 6 digits
                if not (code_str.isdigit() and len(code_str) == 6):
                    continue
                
                # Extract Values
                def get_val(idx):
                    try:
                        val = row[idx]
                        if pd.isna(val): return 0.0
                        return float(val)
                    except:
                        return 0.0

                nilai_perolehan = get_val(6)
                saldo_awal = get_val(7)
                mutasi_tambah = get_val(8)
                mutasi_kurang = get_val(9)
                saldo_akhir = get_val(12)
                
                # Nilai Buku is the last column. 
                # We can find the last valid index, or use -1 if we strip NaNs?
                # The dataframe might have trailing NaN columns. 
                # Let's find the header row length? Or just take the last non-null value?
                # Risk: Last non-null might be 'mutasi' if others are null.
                # Inspection showed it was around index 17. 
                # Let's try to look for the last value in the row that is a number.
                
                # Robust approach for Nilai Buku:
                # Usually it's the right-most numeric column.
                # Let's take the last element of the row, working backwards until we find a number.
                nilai_buku = 0.0
                for val in reversed(row.values):
                    if pd.notna(val):
                        try:
                            nilai_buku = float(val)
                            # Basic validation: data shouldn't be the same as known columns unless coincidence
                            # But usually Nilai Buku is significant.
                            break
                        except:
                            continue

                entry = {
                    "kode_ba": metadata["kode_ba"],
                    "uraian_ba": metadata["uraian_ba"],
                    "tahun_anggaran": metadata["tahun_anggaran"],
                    "jenis": jenis_penyusutan,
                    
                    "kode_akun": code_str,
                    "uraian_akun": str(row[2]).strip() if len(row) > 2 else "",
                    
                    "nilai_perolehan": nilai_perolehan,
                    "saldo_awal_penyusutan": saldo_awal,
                    "mutasi_tambah": mutasi_tambah,
                    "mutasi_kurang": mutasi_kurang,
                    "saldo_akhir_penyusutan": saldo_akhir,
                    "nilai_buku": nilai_buku
                }
                extracted_data.append(entry)
                
            except Exception as e:
                continue
                
        return extracted_data
