from abc import ABC, abstractmethod
import pandas as pd
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
        Parses the header rows (first 10) to find metadata like UAPB/UAKPB.
        Returns a dict with 'kode_ba' and 'uraian_ba'.
        """
        metadata = {"kode_ba": "000", "uraian_ba": "Unknown"}
        
        # Look at first 10 rows
        for idx in range(min(10, len(df))):
            row_values = [str(val).strip() for val in df.iloc[idx].values if pd.notna(val)]
            row_str = " ".join(row_values)
            
            # Check for UAPB or UAKPB marker
            if "UAPB" in row_str or "UAKPB" in row_str:
                # Naive strategy: Look for the first numeric string as code, and the longest string as description?
                # Or based on specific patterns seen in inspection.
                # Pattern often: "UAPB", ":", "001", "MAJELIS..."
                
                parts = row_values
                found_marker = False
                for i, part in enumerate(parts):
                    if "UAPB" in part or "UAKPB" in part:
                        found_marker = True
                        # The marker cell might also contain the code, e.g. "UAPB : 001"
                        # But simpler to just continue and process next parts/sub-parts
                        
                    if found_marker:
                        # Split part by colon to handle ": 001" or "UAPB: 001"
                        # Also replace colon with space to ensure separation
                        sanitized = part.replace(":", " ").replace("UAPB", "").replace("UAKPB", "")
                        sub_parts = sanitized.split()
                        
                        for sub in sub_parts:
                            # Check for code (digits or float-like string)
                            clean_sub = sub.replace(".0", "") if sub.endswith(".0") else sub
                            
                            if clean_sub.isdigit() and metadata["kode_ba"] == "000": 
                                 if len(clean_sub) < 3:
                                     metadata["kode_ba"] = clean_sub.zfill(3)
                                 else:
                                     metadata["kode_ba"] = clean_sub
                                     
                            # If it's text and not the code, assume description
                            # Use original 'part' or 'sub'?
                            # Usually description is a long string. 
                            # If sub is "MAJELIS", it's text.
                            # But we want the full description which might be "MAJELIS PERMUSYAWARATAN RAKYAT"
                            # The description is likely the rest of the parts. 
                            # But if we are iterating sub-parts, we might lose context of the full string if split.
                            
                        # Fallback for description: If part contains text and is not just the code
                        # This is a bit heuristic. Better to capture description after code is found?
                        
                # Second pass or refined pass for description
                # Once code is found, the 'rest' is description?
                if metadata["kode_ba"] != "000":
                    # Re-iterate to find description?
                    # Or just:
                    full_row_str = " ".join(parts)
                    # Find code in the string, everything after is description?
                    # "UAPB : 001 MAJELIS ..."
                    if metadata["kode_ba"] in full_row_str:
                        # Split by code
                        _, remainder = full_row_str.split(metadata["kode_ba"], 1)
                        candidate_desc = remainder.strip().replace(":", "").strip()
                        if len(candidate_desc) > 2:
                             metadata["uraian_ba"] = candidate_desc
                
                # Break after processing the marker row
                if found_marker:
                    break
                
        return metadata
