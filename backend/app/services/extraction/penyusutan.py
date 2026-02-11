from typing import List, BinaryIO
import pandas as pd
from app.services.extraction.base import BaseExtractor

class PenyusutanExtractor(BaseExtractor):
    def extract(self, file_content: BinaryIO, filename: str) -> List[dict]:
        # Penyusutan: Code (Col 0), Desc (Col 2), Value (Last Column usually). Data starts around row 12.
        
        df = pd.read_excel(file_content, header=None)
        
        metadata = self.parse_metadata(df)
        
        extracted_data = []
        
        for index, row in df.iterrows():
            try:
                code_raw = row[0]
                desc_raw = row[2]
                
                if pd.isna(code_raw):
                    continue
                
                code_str = str(code_raw).strip()
                if not code_str.isdigit():
                    continue

                # Value Logic:
                # The last column is "Nilai Buku".
                # Inspecting the row, find the last valid numeric value?
                # Or based on inspection, it was column 10 or 11.
                # Let's try to get the last column of the row.
                # Note: row is a Series with index matching columns.
                # We can filter out NaNs from the end?
                # Or just take the last column of the dataframe if the dataframe has fixed width.
                
                # Based on inspection:
                # 11: 1 NaN 2 ... 9=4-8 (Index 11?)
                # 12: 131111 ... 835960489740 (Index 11?)
                
                val_raw = row.iloc[-1] # Last column
                if pd.isna(val_raw):
                     # Maybe try -2? sometimes there are empty trailing columns
                     val_raw = row.iloc[-2]

                val_float = float(val_raw)
                
                entry = {
                    "kode_akun": code_str,
                    "uraian_akun": str(desc_raw).strip(),
                    "nilai": val_float,
                    "tahun_anggaran": 2023,
                    "kode_ba": metadata["kode_ba"],
                    "uraian_ba": metadata["uraian_ba"]
                }
                extracted_data.append(entry)
                
            except (ValueError, IndexError):
                continue
                
        return extracted_data
