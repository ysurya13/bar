from abc import ABC, abstractmethod
import pandas as pd
import re
from typing import BinaryIO, List
from app.models.extracted_data import ExtractedEntry

class BaseExtractor(ABC):
    """
    Abstract Base Class for all Excel Extractors.
    Each data category (Neraca, Laporan Barang, etc.) will have its own implementation.
    """

    @abstractmethod
    def extract(self, file_content: BinaryIO, filename: str) -> List[dict]:
        """
        Parses the Excel file and returns a list of dictionaries 
        matching the ExtractedEntry model structure.
        
        :param file_content: The file-like object of the uploaded Excel.
        :param filename: The name of the file (useful for metadata).
        :return: List of dicts ready to be inserted into DB.
        """
        pass

    def validate_columns(self, df: pd.DataFrame, required_columns: List[str]) -> bool:
        """
        Helper to validate if required columns exist in the DataFrame.
        """
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")
        return True

    def parse_metadata(self, df: pd.DataFrame) -> dict:
        """
        Parses the header rows (first 10) to find metadata like UAPB/UAKPB and TAHUN ANGGARAN.
        Returns a dict with 'kode_ba', 'uraian_ba', and 'tahun_anggaran'.
        """
        metadata = {
            "kode_ba": "000", 
            "uraian_ba": "Unknown",
            "tahun_anggaran": None  # Default loopback to None, allowing UI override
        }
        
        # Look at first 10 rows
        for idx in range(min(10, len(df))):
            row_values = [str(val).strip() for val in df.iloc[idx].values if pd.notna(val)]
            row_str = " ".join(row_values)
            
            # 1. Search for TAHUN ANGGARAN
            if "TAHUN ANGGARAN" in row_str:
                # Look for a 4-digit year in this row
                for part in row_values:
                    # Case 1: Part is exactly the 4-digit year
                    clean_part = part.replace(":", "").replace("-", "").strip()
                    if clean_part.isdigit() and len(clean_part) == 4:
                        metadata["tahun_anggaran"] = int(clean_part)
                        break
                    
                    # Case 2: Year is inside a string like "TAHUN ANGGARAN 2024"
                    if "TAHUN ANGGARAN" in part:
                        # Find all digit sequences
                        years = re.findall(r'\b(20\d{2})\b', part)
                        if years:
                            metadata["tahun_anggaran"] = int(years[0])
                            break
            
            # 2. Search for UAPB or UAKPB marker
            if "UAPB" in row_str or "UAKPB" in row_str:
                parts = row_values
                marker_in_row = False
                for i, part in enumerate(parts):
                    if "UAPB" in part or "UAKPB" in part:
                        marker_in_row = True
                        
                    if marker_in_row:
                        sanitized = part.replace(":", " ").replace("UAPB", "").replace("UAKPB", "").strip()
                        sub_parts = sanitized.split()
                        
                        for sub in sub_parts:
                            clean_sub = sub.replace(".0", "") if sub.endswith(".0") else sub
                            if clean_sub.isdigit() and metadata["kode_ba"] == "000": 
                                 if len(clean_sub) < 3:
                                     metadata["kode_ba"] = clean_sub.zfill(3)
                                 else:
                                     metadata["kode_ba"] = clean_sub
                
                # Refined pass for description
                if metadata["kode_ba"] != "000" and metadata["uraian_ba"] == "Unknown":
                    full_row_str = " ".join(parts)
                    if metadata["kode_ba"] in full_row_str:
                        _, remainder = full_row_str.split(metadata["kode_ba"], 1)
                        candidate_desc = remainder.strip().replace(":", "").strip()
                        if len(candidate_desc) > 2:
                             metadata["uraian_ba"] = candidate_desc
                
        return metadata
