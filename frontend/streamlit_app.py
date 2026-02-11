import streamlit as st
import pandas as pd
import sys
import os
import plotly.express as px

# Add backend to path to import services
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(current_dir, "..", "backend")
sys.path.append(backend_path)

from app.services.extraction.factory import ExtractorFactory
from app.db.session import SessionLocal
from app.models.extracted_data import ExtractedEntry
import uuid

st.set_page_config(
    page_title="Financial Data Engine",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Multi-Format Excel Data Ingestion & Analytics")
st.markdown("Upload financial reports (Neraca, Saldo Awal, Penyusutan) to extract, analyze, and persist data.")

# Sidebar Configuration
st.sidebar.header("Configuration")
fiscal_year = st.sidebar.selectbox("Fiscal Year", [2023, 2024], index=0)
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
    
    # Initialize Extractor once
    factory = ExtractorFactory()
    extractor = factory.get_extractor(data_category)
    
    processing_placeholder = st.empty()
    
    for uploaded_file in uploaded_files:
        processing_placeholder.info(f"Processing {uploaded_file.name}...")
        try:
            results = extractor.extract(uploaded_file, uploaded_file.name)
            if results:
                # Add filename to each entry for tracking
                for r in results:
                    r['source_file'] = uploaded_file.name
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
                    
                    if i % 10 == 0 or i == total - 1:
                        save_progress.progress((i + 1) / total)
                        status_text.text(f"Saving entry {i+1} of {total}...")
                
                db.commit()
                st.success(f"Successfully saved {total} entries to database! (Upload ID: {upload_uuid})")
                db.close()
            except Exception as e:
                st.error(f"Failed to save data: {e}")
                if 'db' in locals():
                    db.rollback()
                    db.close()
        
        # Simple Visualization
        st.subheader("Analysis")
        if 'nilai' in df.columns and 'uraian_akun' in df.columns:
            # Group by account to handle duplicates across multiple files
            agg_df = df.groupby('uraian_akun')['nilai'].sum().reset_index()
            
            # Top 10 Accounts by Value
            top_10 = agg_df.nlargest(10, 'nilai')
            fig = px.bar(
                top_10, 
                x='nilai', 
                y='uraian_akun', 
                orientation='h',
                title=f"Top 10 Accounts by Consolidated Value ({data_category})",
                labels={'nilai': 'Total Value (IDR)', 'uraian_akun': 'Account Description'}
            )
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
            
        # Export Option
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download Combined CSV",
            csv,
            f"{data_category}_{fiscal_year}_batch_extracted.csv",
            "text/csv",
            key='download-csv'
        )
        
    else:
        st.warning("No data extracted from the uploaded files. Please check the file formats.")


st.divider()
st.caption("Financial Data Engine v1.0 | Powered by Python & Streamlit")
