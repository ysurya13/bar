from typing import List, BinaryIO
import pandas as pd
from app.services.extraction.base import BaseExtractor

class NeracaExtractor(BaseExtractor):
    def extract(self, file_content: BinaryIO, filename: str) -> List[dict]:
        # file_content can be bytes or file-like. Pandas handles it.
        # Neraca: Code (Col 1), Desc (Col 5), Value (Col 8). Data starts around row 9.
        
        # Load excel, no header initially to locate start
        df = pd.read_excel(file_content, header=None)
        
        # Parse Metadata first
        metadata = self.parse_metadata(df)
        
        extracted_data = []
        
        # Iterate rows
        for index, row in df.iterrows():
            # Heuristic: Check if Column 1 contains a numeric code (usually 6 digits)
            # and Column 5 has text.
            try:
                code_raw = row[1]
                desc_raw = row[5]
                val_raw = row[8]
                
                # Check if code is valid (string or int, representing account code)
                # Filter out headers/NaNs
                if pd.isna(code_raw) or pd.isna(val_raw):
                    continue
                
                code_str = str(code_raw).strip()
                
                # Simple validation: Code should be numeric (allow some flexibility if needed)
                if not code_str.isdigit():
                    continue

                val_float = float(val_raw)
                
                entry = {
                    "kode_akun": code_str,
                    "uraian_akun": str(desc_raw).strip(),
                    "nilai": val_float,
                    "tahun_anggaran": 2023, # Default or parsed from Row 1
                    "kode_ba": metadata["kode_ba"],
                    "uraian_ba": metadata["uraian_ba"]
                }
                extracted_data.append(entry)
                
            except (ValueError, IndexError):
                continue
                
        return extracted_data
