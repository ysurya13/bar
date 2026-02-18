from typing import List, BinaryIO
import pandas as pd
import re
from app.services.extraction.base import BaseExtractor


class LaporanBarangExtractor(BaseExtractor):
    """
    Extractor for Laporan Barang files.

    Supports 4 types:
    - Aset Tak Berwujud        (subsubkelompok)
    - Ekstrakomptabel          (kelompok)
    - Intrakomptabel           (kelompok)
    - Konstruksi Dalam Pengerjaan (subsubkelompok)

    All types share the same output schema:
        kode_akun (6-digit), uraian_akun,
        nilai_awal, mutasi_tambah, mutasi_kurang, nilai_akhir,
        jenis_laporan, tahun_anggaran, kode_ba, uraian_ba
    """

    # ------------------------------------------------------------------ #
    # Type detection keywords (checked against first ~5 rows)             #
    # ------------------------------------------------------------------ #
    _TYPE_KEYWORDS = {
        "ASET TAK BERWUJUD":            "Aset Tak Berwujud",
        "EKSTRAKOMPTABEL":              "Ekstrakomptabel",
        "INTRAKOMPTABEL":               "Intrakomptabel",
        "KONTRUKSI DALAM PENGERJAAN":   "Konstruksi Dalam Pengerjaan",  # typo in source
        "KONSTRUKSI DALAM PENGERJAAN":  "Konstruksi Dalam Pengerjaan",
    }

    def _detect_type(self, df: pd.DataFrame) -> str:
        """Return the human-readable laporan type from the first 5 rows."""
        for idx in range(min(5, len(df))):
            row_str = " ".join(
                str(v).upper() for v in df.iloc[idx].values if pd.notna(v)
            )
            for keyword, label in self._TYPE_KEYWORDS.items():
                if keyword in row_str:
                    return label
        return "Unknown"

    def _find_data_start(self, df: pd.DataFrame) -> int:
        """
        Locate the first row that contains an actual 6-digit account code
        in column 0. Returns the row index.
        """
        for idx in range(len(df)):
            val = df.iloc[idx, 0]
            if pd.notna(val):
                code_str = str(val).strip().replace(".0", "")
                if code_str.isdigit() and len(code_str) == 6:
                    return idx
        return 0

    def _get_val(self, row: pd.Series, col_idx: int) -> float:
        """Safely extract a float from a row at a given column index."""
        try:
            val = row.iloc[col_idx] if col_idx < len(row) else None
            if pd.isna(val):
                return 0.0
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    def _get_last_numeric(self, row: pd.Series) -> float:
        """Return the last non-null numeric value in a row (for Nilai Akhir)."""
        for val in reversed(row.values):
            if pd.notna(val):
                try:
                    return float(val)
                except (ValueError, TypeError):
                    continue
        return 0.0

    # ------------------------------------------------------------------ #
    # Column layout per type                                               #
    # ------------------------------------------------------------------ #
    # Layout dict: (col_uraian, col_nilai_awal, col_mutasi_tambah,
    #               col_mutasi_kurang, col_nilai_akhir_or_None)
    # When col_nilai_akhir is None we fall back to _get_last_numeric().
    _LAYOUTS = {
        "Aset Tak Berwujud": {
            "col_uraian":        2,
            "col_nilai_awal":    7,
            "col_mutasi_tambah": 9,
            "col_mutasi_kurang": 11,
            "col_nilai_akhir":   18,   # last NILAI column
        },
        "Ekstrakomptabel": {
            "col_uraian":        4,
            "col_nilai_awal":    7,
            "col_mutasi_tambah": 9,
            "col_mutasi_kurang": 11,
            "col_nilai_akhir":   17,
        },
        "Intrakomptabel": {
            "col_uraian":        4,
            "col_nilai_awal":    7,
            "col_mutasi_tambah": 9,
            "col_mutasi_kurang": 11,
            "col_nilai_akhir":   17,
        },
        "Konstruksi Dalam Pengerjaan": {
            "col_uraian":        2,
            "col_nilai_awal":    6,
            "col_mutasi_tambah": 7,
            "col_mutasi_kurang": 8,
            "col_nilai_akhir":   9,
        },
    }

    # Default layout used when type is unknown (best-effort)
    _DEFAULT_LAYOUT = {
        "col_uraian":        2,
        "col_nilai_awal":    7,
        "col_mutasi_tambah": 9,
        "col_mutasi_kurang": 11,
        "col_nilai_akhir":   None,   # use last numeric
    }

    # ------------------------------------------------------------------ #
    # Main extract method                                                  #
    # ------------------------------------------------------------------ #
    def extract(self, file_content: BinaryIO, filename: str) -> List[dict]:
        df = pd.read_excel(file_content, header=None)

        # 1. Parse metadata (kode_ba, uraian_ba, tahun_anggaran)
        metadata = self.parse_metadata(df)

        # 2. Detect laporan type
        jenis_laporan = self._detect_type(df)

        # 3. Get column layout
        layout = self._LAYOUTS.get(jenis_laporan, self._DEFAULT_LAYOUT)
        col_uraian        = layout["col_uraian"]
        col_nilai_awal    = layout["col_nilai_awal"]
        col_mutasi_tambah = layout["col_mutasi_tambah"]
        col_mutasi_kurang = layout["col_mutasi_kurang"]
        col_nilai_akhir   = layout["col_nilai_akhir"]

        extracted_data: List[dict] = []

        for _, row in df.iterrows():
            try:
                code_raw = row.iloc[0] if len(row) > 0 else None
                if pd.isna(code_raw):
                    continue

                # Normalise: strip trailing ".0" that pandas adds to int-like floats
                code_str = str(code_raw).strip()
                if code_str.endswith(".0"):
                    code_str = code_str[:-2]

                # STRICT: only accept exactly 6-digit numeric codes
                if not (code_str.isdigit() and len(code_str) == 6):
                    continue

                # Uraian
                uraian_raw = row.iloc[col_uraian] if col_uraian < len(row) else ""
                uraian = str(uraian_raw).strip() if pd.notna(uraian_raw) else ""

                # Values
                nilai_awal    = self._get_val(row, col_nilai_awal)
                mutasi_tambah = self._get_val(row, col_mutasi_tambah)
                mutasi_kurang = self._get_val(row, col_mutasi_kurang)

                if col_nilai_akhir is not None:
                    nilai_akhir = self._get_val(row, col_nilai_akhir)
                else:
                    nilai_akhir = self._get_last_numeric(row)

                entry = {
                    "kode_akun":      code_str,
                    "uraian_akun":    uraian,
                    "nilai_awal":     nilai_awal,
                    "mutasi_tambah":  mutasi_tambah,
                    "mutasi_kurang":  mutasi_kurang,
                    "nilai_akhir":    nilai_akhir,
                    "jenis_laporan":  jenis_laporan,
                    "tahun_anggaran": metadata["tahun_anggaran"],
                    "kode_ba":        metadata["kode_ba"],
                    "uraian_ba":      metadata["uraian_ba"],
                }
                extracted_data.append(entry)

            except (ValueError, IndexError):
                continue

        return extracted_data
