import pandas as pd
import os

# Determine project root and base path
base_dir = os.path.dirname(os.path.abspath(__file__))
base_path = os.path.join(base_dir, "excel", "2023")
files_to_inspect = {
    "Neraca": "Neraca/Laporan lap_bmn_nrc kl  kode 001.xlsx",
    "Penyusutan": "Penyusutan/PENYUSUTAN INTRAKOMPTABEL/Laporan lap_susut kl intrakomptabel kelompok kode 001.xlsx",
    "Saldo Awal": "Saldo Awal/Laporan lap_bmn_nrc_sawal kl  kode 001.xlsx"
}

for category, rel_path in files_to_inspect.items():
    full_path = os.path.join(base_path, rel_path)
    if os.path.exists(full_path):
        print(f"\n--- Inspecting {category} ({rel_path}) ---")
        try:
            # Read first 15 rows to capture more header context
            df = pd.read_excel(full_path, header=None, nrows=15)
            print(df.to_string())
        except Exception as e:
            print(f"Error reading {category}: {e}")
    else:
        print(f"File not found: {full_path}")
