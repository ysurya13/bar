import sys
import os
import pandas as pd

# Add backend to path so we can import app modules
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.extraction.factory import ExtractorFactory

# Determine project root and base path
base_dir = os.path.dirname(os.path.abspath(__file__))
base_path = os.path.join(base_dir, "excel", "2023")
files_to_test = {
    "Neraca": "Neraca/Laporan lap_bmn_nrc kl  kode 001.xlsx",
    "Saldo Awal": "Saldo Awal/Laporan lap_bmn_nrc_sawal kl  kode 001.xlsx",
    "Penyusutan": "Penyusutan/PENYUSUTAN INTRAKOMPTABEL/Laporan lap_susut kl intrakomptabel kelompok kode 001.xlsx"
}

def test_extraction():
    factory = ExtractorFactory()
    
    for category, rel_path in files_to_test.items():
        print(f"\nTesting {category}...")
        full_path = os.path.join(base_path, rel_path)
        
        if not os.path.exists(full_path):
            print(f"File not found: {full_path}")
            continue
            
        try:
            extractor = factory.get_extractor(category)
            
            # Read as binary to simulate upload file
            with open(full_path, "rb") as f:
                # We need to pass file object. Pandas read_excel accepts file path or file-like.
                # BaseExtractor expects file-like usually, let's pass the file object or just path if implementation allows.
                # My implementation uses pd.read_excel(file_content) which works with both.
                results = extractor.extract(f, filename=os.path.basename(full_path))
                
            print(f"Extracted {len(results)} entries.")
            if results:
                print("First 3 entries:")
                for entry in results[:3]:
                    print(entry)
            else:
                print("No entries extracted!")
                
        except Exception as e:
            print(f"FAILED: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_extraction()
