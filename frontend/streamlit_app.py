import streamlit as st
import pandas as pd
import sys
import os
import plotly.express as px
import uuid

# Add backend to path to import services
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(current_dir, "..", "backend")
sys.path.append(backend_path)

from app.services.extraction.factory import ExtractorFactory
from app.db.session import SessionLocal
from app.models.extracted_data import ExtractedEntry, BARMetadata, BARNonNeraca, OrganizationPIC
from app.services.reporting.pdf_generator import BARPDFGenerator

# Utility: Get Organization PIC (Counterpart)
def get_organization_pic(kode_ba):
    db = SessionLocal()
    try:
        return db.query(OrganizationPIC).filter(
            OrganizationPIC.kode_ba == kode_ba
        ).first()
    finally:
        db.close()

# Utility: Load Non-Neraca Data
def load_non_neraca_data(kode_ba, tahun):
    db = SessionLocal()
    try:
        results = db.query(BARNonNeraca).filter(
            BARNonNeraca.kode_ba == kode_ba,
            BARNonNeraca.tahun_anggaran == tahun
        ).all()
        return {r.label: {'awal': float(r.nilai_awal), 'akhir': float(r.nilai_akhir)} for r in results}
    finally:
        db.close()

# Utility: Save Non-Neraca Data
def save_non_neraca_data(kode_ba, tahun, labels_values):
    db = SessionLocal()
    try:
        # Delete existing for this BA/Year
        db.query(BARNonNeraca).filter(
            BARNonNeraca.kode_ba == kode_ba,
            BARNonNeraca.tahun_anggaran == tahun
        ).delete()
        
        for label, vals in labels_values.items():
            db_entry = BARNonNeraca(
                kode_ba=kode_ba,
                tahun_anggaran=tahun,
                label=label,
                nilai_awal=vals['awal'],
                nilai_akhir=vals['akhir']
            )
            db.add(db_entry)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        st.error(f"Error saving non-neraca data: {e}")
        return False
    finally:
        db.close()

# Utility: Load BAR Metadata
def load_bar_metadata(kode_ba, tahun):
    db = SessionLocal()
    try:
        return db.query(BARMetadata).filter(
            BARMetadata.kode_ba == kode_ba,
            BARMetadata.tahun_anggaran == tahun
        ).first()
    finally:
        db.close()

# Utility: Save BAR Metadata
def save_bar_metadata(kode_ba, tahun, nama=None, nip=None, ttd_type=None, catatan=None):
    db = SessionLocal()
    try:
        existing = db.query(BARMetadata).filter(
            BARMetadata.kode_ba == kode_ba,
            BARMetadata.tahun_anggaran == tahun
        ).first()
        
        if existing:
            if nama is not None: existing.nama_petugas = nama
            if nip is not None: existing.nip_petugas = nip
            if ttd_type is not None: existing.jenis_ttd = ttd_type
            if catatan is not None: existing.catatan_kualitatif = catatan
        else:
            new_meta = BARMetadata(
                kode_ba=kode_ba,
                tahun_anggaran=tahun,
                nama_petugas=nama,
                nip_petugas=nip,
                jenis_ttd=ttd_type,
                catatan_kualitatif=catatan
            )
            db.add(new_meta)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        st.error(f"Error saving metadata: {e}")
        return False
    finally:
        db.close()

st.set_page_config(
    page_title="Financial Data Engine",
    page_icon="📊",
    layout="wide"
)

# Utility: Load data from DB
def load_db_data():
    db = SessionLocal()
    try:
        query = db.query(ExtractedEntry).all()
        if not query:
            return pd.DataFrame()
        
        data = []
        for entry in query:
            data.append({
                "id": entry.id,
                "upload_id": entry.upload_id,
                "data_category": entry.data_category,
                "kode_akun": entry.kode_akun,
                "uraian_akun": entry.uraian_akun,
                "nilai": float(entry.nilai) if entry.nilai else 0.0,
                "tahun_anggaran": entry.tahun_anggaran,
                "kode_ba": entry.kode_ba,
                "uraian_ba": entry.uraian_ba,
                "created_at": entry.created_at
            })
        return pd.DataFrame(data)
    finally:
        db.close()

# Utility: Simple Asset Categorization
def get_asset_category(row):
    kode = str(row['kode_akun'])
    if kode.startswith('117'): return 'Persediaan'
    if kode.startswith('131'): return 'Tanah'
    if kode.startswith('132'): return 'Peralatan & Mesin'
    if kode.startswith('133'): return 'Gedung & Bangunan'
    if kode.startswith('134'): return 'Jalan, Irigasi & Jaringan'
    if kode.startswith('135'): return 'Aset Tetap Lainnya'
    if kode.startswith('136'): return 'KDP'
    return 'Lainnya'

# Sidebar Navigation
st.sidebar.title("📌 Main Menu")
main_page = st.sidebar.selectbox("Main Category", ["Data Ingestion", "Analytics Dashboard", "Generate BAR"])

if main_page == "Data Ingestion":
    st.sidebar.divider()
    page = "Data Ingestion"
elif main_page == "Analytics Dashboard":
    st.sidebar.divider()
    page = "Analytics Dashboard"
elif main_page == "Generate BAR":
    st.sidebar.divider()
    st.sidebar.subheader("Generate BAR")
    page = st.sidebar.radio("Sub Page", ["Face BAR", "Lampiran Kualitatif", "Lampiran Kuantitatif"])

if page == "Data Ingestion":
    st.title("📊 Data Ingestion")
    st.markdown("Upload financial reports (Neraca, Saldo Awal, Penyusutan) to extract and persist data.")

    # Sidebar Filter for Category
    st.sidebar.divider()
    st.sidebar.header("Upload Settings")
    fiscal_year = st.sidebar.selectbox("Fiscal Year", [2022, 2023, 2024], index=1)
    data_category = st.sidebar.selectbox(
        "Data Category", 
        ["Neraca", "Saldo Awal", "Penyusutan"]
    )

    # File Upload
    st.subheader(f"Upload {data_category} Files")
    uploaded_files = st.file_uploader(
        f"Choose {data_category} Excel files", 
        type=["xlsx", "xls"],
        accept_multiple_files=True
    )

    if uploaded_files:
        all_results = []
        factory = ExtractorFactory()
        extractor = factory.get_extractor(data_category)
        
        processing_placeholder = st.empty()
        
        for uploaded_file in uploaded_files:
            processing_placeholder.info(f"Processing {uploaded_file.name}...")
            try:
                results = extractor.extract(uploaded_file, uploaded_file.name)
                if results:
                    for r in results:
                        r['source_file'] = uploaded_file.name
                        # Use selected year if not parsed
                        if 'tahun_anggaran' not in r:
                            r['tahun_anggaran'] = fiscal_year
                    all_results.extend(results)
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {e}")
                
        processing_placeholder.empty()

        if all_results:
            df = pd.DataFrame(all_results)
            
            # Show Metrics
            total_value = df['nilai'].sum()
            count = len(df)
            file_count = len(uploaded_files)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Files", file_count)
            col2.metric("Total Records", count)
            col3.metric("Total Value (IDR)", f"{total_value:,.0f}")
            
            # Data Preview
            st.subheader("Extracted Data (Consolidated)")
            st.dataframe(df, use_container_width=True)
            
            # Database Integration
            st.subheader("Database Persistence")
            if st.button("💾 Save All Extracted Data to Database", type="primary"):
                save_progress = st.progress(0)
                status_text = st.empty()
                
                try:
                    db = SessionLocal()
                    upload_uuid = str(uuid.uuid4())
                    
                    # Deduplication: Find unique (tahun, ba) pairs in current batch
                    unique_pairs = set((entry.get('tahun_anggaran', fiscal_year), entry.get('kode_ba')) for entry in all_results)
                    
                    for yr, ba in unique_pairs:
                        db.query(ExtractedEntry).filter(
                            ExtractedEntry.tahun_anggaran == yr,
                            ExtractedEntry.kode_ba == ba,
                            ExtractedEntry.data_category == data_category
                        ).delete()
                    
                    db.flush()
                    
                    total = len(all_results)
                    for i, entry in enumerate(all_results):
                        db_entry = ExtractedEntry(
                            upload_id=upload_uuid,
                            data_category=data_category,
                            kode_akun=entry.get('kode_akun'),
                            uraian_akun=entry.get('uraian_akun'),
                            nilai=entry.get('nilai'),
                            tahun_anggaran=entry.get('tahun_anggaran', fiscal_year),
                            kode_ba=entry.get('kode_ba'),
                            uraian_ba=entry.get('uraian_ba')
                        )
                        db.add(db_entry)
                        
                        if i % 100 == 0 or i == total - 1:
                            save_progress.progress((i + 1) / total)
                            status_text.text(f"Saving entry {i+1} of {total}...")
                    
                    db.commit()
                    st.success(f"Successfully saved {total} entries! (Batch ID: {upload_uuid})")
                    db.close()
                except Exception as e:
                    st.error(f"Failed to save data: {e}")
                    if 'db' in locals():
                        db.rollback()
                        db.close()
            
            # Export Option
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Combined CSV", csv, f"{data_category}_batch.csv", "text/csv")
            
        else:
            st.warning("No data extracted. Please check file format.")

elif page == "Analytics Dashboard":
    st.title("📈 Analytics Dashboard")
    st.markdown("Analyze financial assets across Years and Organizations.")

    # Load data
    df_db = load_db_data()

    if df_db.empty:
        st.warning("No data found in database. Please go to 'Data Ingestion' and upload some files first.")
    else:
        # Augment data with Asset Categories
        df_db['jenis_aset'] = df_db.apply(get_asset_category, axis=1)

        # Dashboard Filters
        st.sidebar.divider()
        st.sidebar.header("Filters")
        
        all_bas = sorted([str(x) for x in df_db['uraian_ba'].unique() if pd.notna(x)])
        selected_ba = st.sidebar.multiselect("Select Organization (BA)", all_bas, default=all_bas)
        
        all_years = sorted([int(x) for x in df_db['tahun_anggaran'].unique() if pd.notna(x)])
        selected_years = st.sidebar.multiselect("Select Years", all_years, default=all_years)
        
        all_cats = sorted([str(x) for x in df_db['data_category'].unique() if pd.notna(x)])
        selected_cats = st.sidebar.multiselect("Select Data Category", all_cats, default=all_cats)
        
        all_assets = sorted([str(x) for x in df_db['jenis_aset'].unique() if pd.notna(x)])
        selected_assets = st.sidebar.multiselect("Select Asset Types", all_assets, default=all_assets)

        # Apply Filters
        mask = (
            df_db['uraian_ba'].isin(selected_ba) & 
            df_db['tahun_anggaran'].isin(selected_years) &
            df_db['data_category'].isin(selected_cats) &
            df_db['jenis_aset'].isin(selected_assets)
        )
        filtered_df = df_db[mask]

        if filtered_df.empty:
             st.info("No data matches the selected filters.")
        else:
            # Summary Metrics
            total_assets = filtered_df['nilai'].sum()
            ba_count = len(filtered_df['uraian_ba'].unique())
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Asset Value", f"IDR {total_assets:,.0f}")
            m2.metric("Filtered Organizations", ba_count)
            m3.metric("Filtered Records", len(filtered_df))

            st.divider()

            # Row 1: Asset Growth & Category Composition
            c1, c2 = st.columns(2)

            with c1:
                st.subheader("Asset Value Growth by Year")
                growth_df = filtered_df.groupby('tahun_anggaran')['nilai'].sum().reset_index()
                fig_growth = px.line(
                    growth_df, x='tahun_anggaran', y='nilai', 
                    markers=True, title="Total Asset Value per Fiscal Year",
                    labels={'nilai': 'Total Value (IDR)', 'tahun_anggaran': 'Year'}
                )
                st.plotly_chart(fig_growth, use_container_width=True)

            with c2:
                st.subheader("Asset Composition by Type")
                comp_df = filtered_df.groupby('jenis_aset')['nilai'].sum().reset_index()
                fig_comp = px.pie(
                    comp_df, values='nilai', names='jenis_aset', 
                    title="Asset Value distribution",
                    hole=0.4
                )
                st.plotly_chart(fig_comp, use_container_width=True)

            # Row 2: BA Comparison
            st.subheader("Organization (BA) Comparison")
            comparison_df = filtered_df.groupby('uraian_ba')['nilai'].sum().reset_index()
            fig_ba = px.bar(
                comparison_df, x='uraian_ba', y='nilai',
                title="Total Assets per Organization",
                labels={'nilai': 'Total Value (IDR)', 'uraian_ba': 'Organization Name'},
                color='nilai', color_continuous_scale='Viridis'
            )
            fig_ba.update_layout(xaxis={'categoryorder':'total descending'})
            st.plotly_chart(fig_ba, use_container_width=True)

            # Row 3: Waterfall Analysis
            st.divider()
            st.header("🌊 Period Change Analysis (Waterfall)")
            st.markdown("Comparing **Saldo Awal** (Start) vs **Neraca** (End) for the selected organizations.")
            
            # Select single year for waterfall
            if len(selected_years) > 0:
                wf_year = st.selectbox("Select Year for Waterfall Analysis", selected_years, index=0)
                
                # Filter data for this year and selected organizations
                wf_df = df_db[
                    (df_db['tahun_anggaran'] == wf_year) & 
                    (df_db['uraian_ba'].isin(selected_ba))
                ]
                
                # Pivot to get categories and values per type
                start_mask = wf_df['data_category'] == 'Saldo Awal'
                end_mask = wf_df['data_category'] == 'Neraca'
                
                start_vals = wf_df[start_mask].groupby('jenis_aset')['nilai'].sum()
                end_vals = wf_df[end_mask].groupby('jenis_aset')['nilai'].sum()
                
                # Get unique asset types present in either
                all_asset_types = sorted(list(set(start_vals.index) | set(end_vals.index)))
                
                if not all_asset_types:
                    st.info("No 'Saldo Awal' or 'Neraca' data found for the selected filters to perform waterfall analysis.")
                else:
                    # Calculate Deltas
                    x_labels = ["Total Saldo Awal"]
                    y_vals = [start_vals.sum()]
                    measures = ["absolute"]
                    
                    for asset_type in all_asset_types:
                        s = start_vals.get(asset_type, 0)
                        e = end_vals.get(asset_type, 0)
                        delta = e - s
                        if delta != 0:
                            x_labels.append(asset_type)
                            y_vals.append(delta)
                            measures.append("relative")
                    
                    x_labels.append("Total Neraca")
                    y_vals.append(end_vals.sum())
                    measures.append("total")
                    
                    import plotly.graph_objects as go
                    fig_wf = go.Figure(go.Waterfall(
                        name="Asset Change",
                        orientation="v",
                        measure=measures,
                        x=x_labels,
                        textposition="outside",
                        text=[f"{y:,.0f}" for y in y_vals],
                        y=y_vals,
                        connector={"line":{"color":"rgb(63, 63, 63)"}},
                        totals={"marker":{"color":"deepskyblue"}}
                    ))

                    fig_wf.update_layout(
                        title=f"Asset Change Bridge: Saldo Awal vs Neraca ({wf_year})",
                        showlegend=False,
                        height=600
                    )
                    st.plotly_chart(fig_wf, use_container_width=True)
            else:
                st.info("Please select at least one year in filters to see waterfall analysis.")

            # Detailed Table
            st.divider()
            st.subheader("Filtered Asset Details")
            st.dataframe(filtered_df, use_container_width=True)

elif page == "Face BAR":
    st.title("📄 Face BAR (Berita Acara Rekonsiliasi)")
    st.markdown("Enter reporting metadata and signing officer details.")

    df_db = load_db_data()
    if df_db.empty:
        st.warning("No data found. Please upload data first.")
    else:
        # Selection for specific BA and Year
        all_bas = sorted([str(x) for x in df_db['uraian_ba'].unique() if pd.notna(x)])
        all_years = sorted([int(x) for x in df_db['tahun_anggaran'].unique() if pd.notna(x)])
        
        col1, col2 = st.columns(2)
        with col1:
            sel_ba_name = st.selectbox("Select Organization (BA)", all_bas)
            # Find kode_ba for the selected name
            sel_ba_code = df_db[df_db['uraian_ba'] == sel_ba_name]['kode_ba'].iloc[0]
        with col2:
            sel_year = st.selectbox("Select Fiscal Year", all_years)

        # Load existing metadata and counterpart
        existing_meta = load_bar_metadata(sel_ba_code, sel_year)
        counterpart_pic = get_organization_pic(sel_ba_code)
        
        st.divider()
        st.subheader("Current Status")
        col_st1, col_st2 = st.columns(2)
        
        with col_st1:
            st.markdown("##### **Assigned Officer (K/L)**")
            if existing_meta and existing_meta.nama_petugas:
                st.success(f"""
                **Name:** {existing_meta.nama_petugas}  
                **NIP:** {existing_meta.nip_petugas}  
                **Signature:** {existing_meta.jenis_ttd}
                """)
            else:
                st.info("⚠️ **No Officer Assigned**")
                
        with col_st2:
            st.markdown("##### **Counterpart Officer (PKKN)**")
            if counterpart_pic:
                st.success(f"""
                **Name:** {counterpart_pic.nama_pic}  
                **NIP:** {counterpart_pic.nip_pic}  
                **Jabatan:** {counterpart_pic.jabatan_pic}
                """)
            else:
                st.info("⚠️ **No Counterpart Found**")

        st.subheader("Signing Officer Details")
        
        with st.form("face_bar_form"):
            nama = st.text_input("Officer Name", value=existing_meta.nama_petugas if existing_meta else "")
            nip = st.text_input("Officer Identification Number (NIP)", value=existing_meta.nip_petugas if existing_meta else "")
            ttd_type = st.radio("Signature Type", ["Elektronik", "Manual"], 
                              index=0 if not existing_meta or existing_meta.jenis_ttd == "Elektronik" else 1)
            
            submitted = st.form_submit_button("💾 Save BAR Metadata", type="primary")
            if submitted:
                if save_bar_metadata(sel_ba_code, sel_year, nama=nama, nip=nip, ttd_type=ttd_type):
                    st.success("BAR Metadata saved successfully!")
                    st.rerun()

        st.divider()
        st.subheader("Asset Balance Summary")
        
        # 1. Load Reference Mapping
        ref_path = "/Users/yusufpradana/Documents/apps/bar/referensi/referensi_face_bar.xlsx"
        df_ref = pd.read_excel(ref_path)
        df_ref['kode_akun_str'] = df_ref['kode_akun'].astype(str)
        
        # 2. Filter DB data for selected BA/Year
        df_target = df_db[
            (df_db['kode_ba'] == sel_ba_code) & 
            (df_db['tahun_anggaran'] == sel_year)
        ].copy()
        df_target['kode_akun_str'] = df_target['kode_akun'].astype(str)
        
        # Merge with reference to get report labels
        df_mapped = pd.merge(df_target, df_ref, on='kode_akun_str', how='inner')
        
        # Part I Labels
        part_i_labels = [
            "Persediaan", "Tanah", "Peralatan dan Mesin", "Gedung dan Bangunan",
            "Jalan, Irigasi, dan Jaringan", "Aset Tetap Lainnya", "Konstruksi Dalam Pengerjaan",
            "Aset Konsesi Jasa Partisipasi Pemerintah", "Aset Konsesi Jasa Pemerintah Partisipasi Mitra (BMN)", 
            "Akum. Penyusutan Aset Tetap", "Properti Investasi", "Akum. Penyusutan Properti Investasi",
            "Kemitraan Dengan Pihak Ketiga", "Aset Tak Berwujud", "Aset lain-lain",
            "Akum. Penyusutan Aset Lainnya"
        ]
        
        part_i_data = {}
        for label in part_i_labels:
            mask_label = df_mapped['akun_spesifik_face_bar'] == label
            awal = float(df_mapped[mask_label & (df_mapped['data_category'] == 'Saldo Awal')]['nilai'].sum())
            akhir = float(df_mapped[mask_label & (df_mapped['data_category'] == 'Neraca')]['nilai'].sum())
            part_i_data[label] = {'awal': awal, 'akhir': akhir}

        # 4. Load Part II existing data
        part_ii_labels = [
            "BMN Ekstrakomptabel", "Akum. Peny. Ekstrakomptabel",
            "BPYBDS", "BARANG HILANG", "BARANG RUSAK BERAT",
            "BARANG PERSEDIAAN YANG DISERAHKAN", "BARANG PERSEDIAAN RUSAK/USANG"
        ]
        existing_part_ii = load_non_neraca_data(sel_ba_code, sel_year)
        
        # 5. UI: Part II Manual Entry Form
        st.markdown("#### Part II - BMN Non Neraca (Manual Input)")
        new_part_ii_values = {}
        with st.form("non_neraca_form"):
            for i, label in enumerate(part_ii_labels):
                st.markdown(f"**{label}**")
                col_awal, col_akhir = st.columns(2)
                with col_awal:
                    v_awal = st.number_input(
                        f"Saldo Awal", 
                        value=float(existing_part_ii.get(label, {}).get('awal', 0.0)),
                        format="%.2f",
                        key=f"val_awal_{label}"
                    )
                with col_akhir:
                    v_akhir = st.number_input(
                        f"Saldo Akhir", 
                        value=float(existing_part_ii.get(label, {}).get('akhir', 0.0)),
                        format="%.2f",
                        key=f"val_akhir_{label}"
                    )
                new_part_ii_values[label] = {'awal': v_awal, 'akhir': v_akhir}
                st.divider()
            
            save_ii = st.form_submit_button("💾 Save Non-Neraca Data", type="secondary")
            if save_ii:
                if save_non_neraca_data(sel_ba_code, sel_year, new_part_ii_values):
                    st.success("Non-Neraca values saved!")
                    st.rerun()

        # 6. Display Consolidated Results
        st.markdown("#### Consolidated Asset Balance Summary")
        
        summary_rows = []
        def fmt(x): return f"{x:,.2f}"

        # Part I Rows
        for label in part_i_labels:
            vals = part_i_data[label]
            awal = float(vals['awal'])
            akhir = float(vals['akhir'])
            mutasi = akhir - awal
            summary_rows.append({
                "Category": label,
                "Saldo Awal": awal,
                "Mutasi": mutasi,
                "Saldo Akhir": akhir,
                "Part": "I - Neraca"
            })
            
        # Part II Rows
        for label in part_ii_labels:
            vals = new_part_ii_values[label]
            awal = float(vals['awal'])
            akhir = float(vals['akhir'])
            mutasi = akhir - awal
            summary_rows.append({
                "Category": label,
                "Saldo Awal": awal,
                "Mutasi": mutasi,
                "Saldo Akhir": akhir,
                "Part": "II - Non Neraca"
            })
            
        df_summary = pd.DataFrame(summary_rows)
        
        # Calculate Totals
        total_awal_i = float(sum(r['Saldo Awal'] for r in summary_rows if r['Part'] == "I - Neraca"))
        total_mutasi_i = float(sum(r['Mutasi'] for r in summary_rows if r['Part'] == "I - Neraca"))
        total_akhir_i = float(sum(r['Saldo Akhir'] for r in summary_rows if r['Part'] == "I - Neraca"))
        
        total_awal_ii = float(sum(r['Saldo Awal'] for r in summary_rows if r['Part'] == "II - Non Neraca"))
        total_mutasi_ii = float(sum(r['Mutasi'] for r in summary_rows if r['Part'] == "II - Non Neraca"))
        total_akhir_ii = float(sum(r['Saldo Akhir'] for r in summary_rows if r['Part'] == "II - Non Neraca"))
        
        st.dataframe(df_summary, use_container_width=True)
        
        # Metrics Display
        st.markdown("---")
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.write("**Total Part I (Neraca)**")
            st.metric("Awal", fmt(total_awal_i))
            st.metric("Mutasi", fmt(total_mutasi_i), delta=fmt(total_mutasi_i))
            st.metric("Akhir", fmt(total_akhir_i))
            
        with m_col2:
            st.write("**Total Part II (Non-Neraca)**")
            st.metric("Awal", fmt(total_awal_ii))
            st.metric("Mutasi", fmt(total_mutasi_ii), delta=fmt(total_mutasi_ii))
            st.metric("Akhir", fmt(total_akhir_ii))

        with m_col3:
            st.write("**GRAND TOTAL (I + II)**")
            st.metric("Total Awal", fmt(total_awal_i + total_awal_ii))
            st.metric("Total Mutasi", fmt(total_mutasi_i + total_mutasi_ii))
            st.metric("Total Akhir", fmt(total_akhir_i + total_akhir_ii))
        
        st.divider()
        st.markdown(f"**Target BA:** {sel_ba_name} ({sel_ba_code})")
        st.markdown(f"**Fiscal Year:** {sel_year}")
        
        # 7. PDF Download
        st.divider()
        st.subheader("Download Report")
        existing_meta = load_bar_metadata(sel_ba_code, sel_year)
        counterpart_pic = get_organization_pic(sel_ba_code)
        
        pdf_gen = BARPDFGenerator()
        pdf_bytes = pdf_gen.generate_bar_pdf(existing_meta, df_summary, sel_ba_name, sel_year, counterpart_pic=counterpart_pic)
        
        st.download_button(
            label="📄 Download BAR (PDF)",
            data=pdf_bytes,
            file_name=f"BAR_{sel_ba_code}_{sel_year}.pdf",
            mime="application/pdf"
        )

elif page == "Lampiran Kualitatif":
    st.title("📝 Lampiran Kualitatif")
    st.markdown("Provide qualitative analysis and explanations for the BAR.")
    
    df_db = load_db_data()
    if df_db.empty:
        st.warning("No data found. Please upload data first.")
    else:
        all_bas = sorted([str(x) for x in df_db['uraian_ba'].unique() if pd.notna(x)])
        all_years = sorted([int(x) for x in df_db['tahun_anggaran'].unique() if pd.notna(x)])
        
        col1, col2 = st.columns(2)
        with col1:
            sel_ba_name = st.selectbox("Select Organization (BA)", all_bas, key="qual_ba")
            sel_ba_code = df_db[df_db['uraian_ba'] == sel_ba_name]['kode_ba'].iloc[0]
        with col2:
            sel_year = st.selectbox("Select Fiscal Year", all_years, key="qual_year")

        # Load existing metadata
        existing_meta = load_bar_metadata(sel_ba_code, sel_year)
        
        st.divider()
        st.subheader("Qualitative Notes")
        catatan_kualitatif = st.text_area(
            "Analysis / Explanation", 
            value=existing_meta.catatan_kualitatif if existing_meta and existing_meta.catatan_kualitatif else "",
            height=300, 
            placeholder="Enter qualitative explanation here..."
        )
        if st.button("💾 Save Qualitative Notes", type="primary"):
            if save_bar_metadata(sel_ba_code, sel_year, catatan=catatan_kualitatif):
                st.success("Qualitative notes saved successfully!")
                st.rerun()

elif page == "Lampiran Kuantitatif":
    st.title("🔢 Lampiran Kuantitatif")
    st.info("Detailed quantitative tables will be added here.")

st.divider()
st.caption("Multi-Format Excel Data Ingestion & Analytics Engine v1.1")
