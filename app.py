import streamlit as st
import pandas as pd

# ==========================================
# KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(page_title="Radar Dividend Capture", page_icon="🎯", layout="wide")

# CSS untuk memadatkan tampilan
st.markdown("""
    <style>
    .block-container { padding-top: 2.5rem; padding-bottom: 1.5rem; }
    [data-testid="stSidebar"] { padding-top: 1rem; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# FUNGSI PEMROSESAN DATA
# ==========================================
@st.cache_data
def process_data(df):
    df = df.dropna(subset=['Cum Date'])
    df['Dividend'] = df['Dividend'].astype(str).str.replace('Rp', '', regex=False).str.replace(',', '').str.strip()
    df['Dividend'] = pd.to_numeric(df['Dividend'], errors='coerce')
    df['Last Price'] = df['Last Price'].astype(str).str.replace(',', '').str.strip()
    df['Last Price'] = pd.to_numeric(df['Last Price'], errors='coerce')
    df['Cum Date'] = pd.to_datetime(df['Cum Date'], errors='coerce')
    df = df.dropna(subset=['Cum Date', 'Dividend', 'Last Price'])
    
    df['Yield (%)'] = (df['Dividend'] / df['Last Price']) * 100
    df['Proyeksi Cum Date'] = df['Cum Date'] + pd.DateOffset(years=1)
    df['Mulai Beli'] = df['Proyeksi Cum Date'] - pd.DateOffset(months=3)
    df['Akhir Beli'] = df['Proyeksi Cum Date'] - pd.DateOffset(months=2)
    df['Bulan Mulai Beli'] = df['Mulai Beli'].dt.strftime('%B %Y')
    
    return df

# ==========================================
# ANTARMUKA PENGGUNA (USER INTERFACE)
# ==========================================
st.markdown("### 🎯 Tools Mencari Gain dengan Radar Dividend ala illusix")

with st.expander("ℹ️ Cara Kerja Aplikasi (Klik untuk melihat)", expanded=False):
    st.markdown("""
    Aplikasi ini dirancang untuk membantu Anda menemukan peluang keuntungan (*capital gain*) dan dividen dari pasar saham. 
    Dengan menghitung mundur 2 hingga 3 bulan sebelum jadwal pembagian dividen (*Cum Date*) tahun depan, 
    Anda dapat mengidentifikasi **Jendela Beli** yang ideal untuk mulai mengoleksi saham sebelum harganya berpotensi naik.
    """)

# SIDEBAR: SUMBER DATA
with st.sidebar:
    st.markdown("### 📂 Sumber Data")
    uploaded_file = st.file_uploader("Unggah file CSV pantauan saham", type=['csv'])

# LOGIKA UTAMA
if uploaded_file is None:
    st.info("👋 Halo! Untuk memulai, silakan unggah file CSV Anda di menu samping (sidebar).")
else:
    try:
        raw_df = pd.read_csv(uploaded_file)
        df_processed = process_data(raw_df)
        
        col1, col2, col3 = st.columns([2, 2, 1.5]) 
        with col1:
            min_yield = st.number_input("Minimal Yield (%)", min_value=0.0, value=5.0, step=0.5)
        with col2:
            opsi_bulan = sorted(df_processed['Bulan Mulai Beli'].unique())
            pilih_bulan = st.multiselect("Pilih Bulan Mulai Beli", options=opsi_bulan, default=[])
        
        df_filtered = df_processed[df_processed['Yield (%)'] >= min_yield]
        if pilih_bulan:
            df_filtered = df_filtered[df_filtered['Bulan Mulai Beli'].isin(pilih_bulan)]
            
        with col3:
            st.metric(label="📊 Total saham lolos", value=len(df_filtered))
        
        # TAMPILKAN HASIL
        if not df_filtered.empty:
            df_display = df_filtered.copy()
            df_display['Jendela Beli'] = df_display['Mulai Beli'].dt.strftime('%d %b %Y') + " s/d " + df_display['Akhir Beli'].dt.strftime('%d %b %Y')
            df_display['Cum Date (Historis)'] = df_display['Cum Date'].dt.strftime('%d %b %Y')
            df_display['Proyeksi Cum Date'] = df_display['Proyeksi Cum Date'].dt.strftime('%d %b %Y')
            df_display['Yield (%)'] = df_display['Yield (%)'].round(2)
            
            kolom_tampil = ['Symbol', 'Cum Date (Historis)', 'Dividend', 'Yield (%)', 'Proyeksi Cum Date', 'Jendela Beli']
            df_display = df_display[kolom_tampil]
            df_display = df_display.sort_values(by='Yield (%)', ascending=False).reset_index(drop=True)
            
            # --- 1. TABEL DITAMPILKAN LEBIH DULU ---
            st.write("### 📋 Detail Jendela Beli")
            st.dataframe(df_display, use_container_width=True, height=200) 
            
            # --- 2. GRAFIK DITAMPILKAN DI BAWAH TABEL ---
            st.write("### 📈 Perbandingan Yield (%)")
            st.bar_chart(data=df_display, x='Symbol', y='Yield (%)', use_container_width=True)
            
        else:
            st.warning("⚠️ Tidak ada saham yang memenuhi kriteria filter Anda.")

    except Exception as e:
        st.error("❌ Terjadi kesalahan saat memproses file Anda. Pastikan format CSV sesuai.")
        st.error(f"Detail error: {e}")