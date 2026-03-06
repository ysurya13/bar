# Excel Data Processing & Reporting System Documentation

## Overview
This system is an automated platform designed to ingest financial reports (Excel) from MONSAKTI, extract structured data, persist it to a PostgreSQL database, and generate formatted Berita Acara Rekonsiliasi (BAR) reports.

## Architecture
The system follows a modular architecture:
- **Frontend**: Streamlit-based web interface for data ingestion, analytics, and report generation.
- **Backend Service Layer**: Python modules for Excel extraction, PDF generation, and database interactions.
- **Database**: PostgreSQL storing extracted entries, metadata, and reference data.

---

## 1. Data Extraction Logic
The system handles various Excel formats through a factory pattern and specialized extractors.

### Base Extractor (`BaseExtractor`)
Provides shared functionality, most importantly `parse_metadata`:
- **Heuristics**: Scans the first 10 rows for keywords.
- **Tahun Anggaran**: Detects 4-digit years near "TAHUN ANGGARAN".
- **Kode BA**: Detects "UAPB" or "UAKPB" markers to extract the 3-digit Agency Code.

### Specialized Extractors
- **NeracaExtractor**: Extracts account codes, descriptions, and values from specific columns (Col 1, 5, 8).
- **SaldoAwalExtractor**: Extracts from Col 0, 4, 7.
- **PenyusutanExtractor**: Handles "Intrakomptabel" vs "Ekstrakomptabel" detection. Robustly identifies "Nilai Buku" by scanning the last numeric column of each row.
- **LaporanBarangExtractor**: Supports multiple sub-types:
    - *Aset Tak Berwujud*
    - *Ekstrakomptabel*
    - *Intrakomptabel*
    - *Konstruksi Dalam Pengerjaan (KDP)*
  Each has a predefined column layout (`_LAYOUTS`) for accurate extraction.

---

## 2. Database Schema & Relations
Data is linked primarily using `kode_ba` (Agency Code) and `tahun_anggaran` (Fiscal Year).

### Core Tables
- `extracted_entries`: General financial data for Neraca and Saldo Awal.
- `penyusutan_entries`: Specific fields for depreciation data (Nilai Perolehan, Mutasi, etc.).
- `laporan_barang_entries`: Specific fields for various item reports.
- `bar_metadata`: Stores officer details (Pihak Kedua) and report settings for a specific BA/Year.
- `bar_non_neraca`: Stores manually entered data for "BMN Non-Neraca" sections.
- `organization_pics`: Reference table linking `kode_ba` to their assigned PKKN counterparts (Pihak Pertama).

### Data Persistence Strategy
The system employs a "Delete-before-Save" strategy to prevent duplication. When new data for a specific `kode_ba` and `tahun_anggaran` is uploaded, existing records for that same pair are removed before the new batch is committed.

---

## 3. Report Generation (PDF BAR)
The `BARPDFGenerator` service creates the official "Berita Acara Rekonsiliasi" using `reportlab`.

### Process:
1. **Data Aggregation**: Summarizes values from `extracted_entries` and `bar_non_neraca`.
2. **Account Mapping**: Uses `referensi_face_bar.xlsx` to map raw account codes to human-readable report labels (e.g., "Tanah", "Persediaan").
3. **Template Logic**:
    - **Header**: Includes official Kemenkeu/DJKN kop.
    - **Narrative**: Generates legal wording with dynamic names/dates.
    - **Financial Tables**: Consolidates balance summaries for Part I (Neraca) and Part II (Non-Neraca).
    - **Signatures**: Supports both Electronic and Manual signature placeholders.

---

## 4. Maintenance & Operations

### Updating Reference Data
Reference data (Accounts, Organizations, PICs) can be updated by modifying the Excel files in the `referensi/` directory and running the import scripts:
```bash
python import_all_reference_data.py
```

### Running the System
- **Backend API (Optional/Future)**: `uvicorn app.main:app`
- **Application**: `streamlit run frontend/streamlit_app.py`

### Key Files
- `backend/app/models/extracted_data.py`: Central schema definition.
- `backend/app/services/extraction/`: Extraction logic by category.
- `frontend/streamlit_app.py`: Main application logic and UI.
