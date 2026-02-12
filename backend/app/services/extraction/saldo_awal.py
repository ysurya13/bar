from typing import List, BinaryIO
import pandas as pd
from app.services.extraction.base import BaseExtractor

class SaldoAwalExtractor(BaseExtractor):
    def extract(self, file_content: BinaryIO, filename: str) -> List[dict]:
        # Saldo Awal: Code (Col 0), Desc (Col 4), Value (Col 7). Data starts around row 8.
        
        df = pd.read_excel(file_content, header=None)
        
        metadata = self.parse_metadata(df)
        
        extracted_data = []
        
        for index, row in df.iterrows():
            try:
                # Adjust indices based on inspection
                code_raw = row[0]
                desc_raw = row[4]
                val_raw = row[7]
                
                if pd.isna(code_raw) or pd.isna(val_raw):
                    continue
                
                code_str = str(code_raw).strip()
                
                # Only take rows where code looks like an account code
                if not code_str.isdigit():
                    continue
                    
                val_float = float(val_raw)
                
                entry = {
                    "kode_akun": code_str,
                    "uraian_akun": str(desc_raw).strip(),
                    "nilai": val_float,
                    "tahun_anggaran": metadata["tahun_anggaran"],
                    "kode_ba": metadata["kode_ba"],
                    "uraian_ba": metadata["uraian_ba"]
                }
                extracted_data.append(entry)
                
            except (ValueError, IndexError):
                continue
                
        return extracted_data
