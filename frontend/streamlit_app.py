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
from app.models.extracted_data import ExtractedEntry

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
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Data Ingestion", "Analytics Dashboard"])

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
                    
                    total = len(all_results)
                    for i, entry in enumerate(all_results):
                        db_entry = ExtractedEntry(
                            upload_id=upload_uuid,
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
        
        all_bas = sorted(df_db['uraian_ba'].unique())
        selected_ba = st.sidebar.multiselect("Select Organization (BA)", all_bas, default=all_bas)
        
        all_years = sorted(df_db['tahun_anggaran'].unique())
        selected_years = st.sidebar.multiselect("Select Years", all_years, default=all_years)
        
        all_categories = sorted(df_db['jenis_aset'].unique())
        selected_categories = st.sidebar.multiselect("Select Asset Types", all_categories, default=all_categories)

        # Apply Filters
        mask = (
            df_db['uraian_ba'].isin(selected_ba) & 
            df_db['tahun_anggaran'].isin(selected_years) &
            df_db['jenis_aset'].isin(selected_categories)
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

            # Detailed Table
            st.subheader("Filtered Asset Details")
            st.dataframe(filtered_df, use_container_width=True)

st.divider()
st.caption("Multi-Format Excel Data Ingestion & Analytics Engine v1.1")
