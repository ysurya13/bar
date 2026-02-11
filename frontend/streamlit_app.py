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

st.set_page_config(
    page_title="Financial Data Engine",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Multi-Format Excel Data Ingestion & Analytics")
st.markdown("Upload financial reports (Neraca, Saldo Awal, Penyusutan) to extract and analyze data.")

# Sidebar Configuration
st.sidebar.header("Configuration")
fiscal_year = st.sidebar.selectbox("Fiscal Year", [2023, 2024], index=0)
data_category = st.sidebar.selectbox(
    "Data Category", 
    ["Neraca", "Saldo Awal", "Penyusutan"]
)

# File Upload
st.subheader(f"Upload {data_category} File")
uploaded_file = st.file_uploader(f"Choose a {data_category} Excel file", type=["xlsx", "xls"])

if uploaded_file is not None:
    st.info(f"Processing {uploaded_file.name}...")
    
    try:
        # Initialize Extractor
        factory = ExtractorFactory()
        extractor = factory.get_extractor(data_category)
        
        # Extract Data
        # We need to reset file pointer if used multiple times, but here it's fresh
        results = extractor.extract(uploaded_file, uploaded_file.name)
        
        if results:
            df = pd.DataFrame(results)
            
            # Show Metrics
            total_value = df['nilai'].sum()
            count = len(df)
            
            col1, col2 = st.columns(2)
            col1.metric("Total Records", count)
            col1.metric("Total Value (IDR)", f"{total_value:,.0f}")
            
            # Data Preview
            st.subheader("Extracted Data")
            st.dataframe(df, use_container_width=True)
            
            # Simple Visualization
            st.subheader("Analysis")
            if 'nilai' in df.columns and 'uraian_akun' in df.columns:
                # Top 10 Accounts by Value
                top_10 = df.nlargest(10, 'nilai')
                fig = px.bar(
                    top_10, 
                    x='nilai', 
                    y='uraian_akun', 
                    orientation='h',
                    title=f"Top 10 Accounts by Value ({data_category})",
                    labels={'nilai': 'Value (IDR)', 'uraian_akun': 'Account Description'}
                )
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
                
            # Export Option
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download as CSV",
                csv,
                f"{data_category}_{fiscal_year}_extracted.csv",
                "text/csv",
                key='download-csv'
            )
            
        else:
            st.warning("No data extracted. Please check the file format.")
            
    except Exception as e:
        st.error(f"Error during extraction: {e}")
        import traceback
        st.code(traceback.format_exc())

st.divider()
st.caption("Financial Data Engine v1.0 | Powered by Python & Streamlit")
