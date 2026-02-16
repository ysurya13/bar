# Reference Data Import Instructions

## Problem
The "Generate BAR" page shows "No Counterpart Found" because the `organization_pics` table is empty.

## Solution
Run the import script to populate all reference data from Excel files into the PostgreSQL database.

## How to Run

1. **Make sure your backend is running** and can connect to the Neon PostgreSQL database.

2. **Run the import script**:
```bash
cd /Users/yusufpradana/Documents/apps/bar
PYTHONPATH=./backend ./.venv/bin/python3 import_all_reference_data.py
```

3. **Refresh your Streamlit app** and check the "Generate BAR" page again.

## What the Script Does

The script imports three types of reference data:

### 1. PKKN Counterpart Officers (`organization_pics` table)
- **Source Files**: 
  - `referensi/referensi_penandatangan_pkkn.xlsx` (PKKN officer details)
  - `referensi/referensi_pic_kl.xlsx` (mapping of organizations to officers)
- **Purpose**: Shows the PKKN counterpart officer for each organization (BA) on the "Generate BAR" page

### 2. Reference Accounts (`ref_accounts` table)
- **Source File**: `referensi/referensi_akun.xlsx`
- **Purpose**: Account code definitions and mappings

### 3. Reference Organizations (`ref_organizations` table)
- **Source File**: `referensi/referensi_kl.xlsx`
- **Purpose**: Organization (BA) code and name mappings

## Expected Output

When you run the script successfully, you should see:

```
==============================================================
  IMPORTING ALL REFERENCE DATA TO POSTGRESQL
==============================================================

==============================================================
IMPORTING PKKN COUNTERPART OFFICERS
==============================================================
Loaded 3 PKKN officers
Loaded 109 organization assignments
Merged 109 organization-officer assignments
Cleared 0 existing records
✓ Successfully imported 109 PKKN counterpart officers

Sample records:
  BA 001: Emirenciana Nyantyasningsih
  BA 002: Darnadi
  BA 004: Emirenciana Nyantyasningsih
  ...

==============================================================
IMPORTING REFERENCE ACCOUNTS
==============================================================
...

==============================================================
✓ ALL IMPORTS COMPLETED SUCCESSFULLY
==============================================================
```

## Verification

After running the script, you can verify the data in your Streamlit app:

1. Go to **Generate BAR** > **Face BAR**
2. Select an organization
3. You should now see the **Counterpart Officer (PKKN)** information populated with:
   - Name
   - NIP
   - Jabatan (Position)

## Troubleshooting

If you see a connection timeout error, check:
- Is your backend server running?
- Can you connect to the Neon database from other scripts?
- Check the `DATABASE_URL` in `backend/app/core/config.py`
