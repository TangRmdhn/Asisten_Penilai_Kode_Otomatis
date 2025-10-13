# app.py
# File ini adalah antarmuka pengguna (UI) menggunakan Streamlit.

import io
import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
# --- PERUBAHAN UTAMA: IMPORT GROQ ---
from groq import Groq

# Import fungsi-fungsi dari file 'otak'
from penilai_otomatis_groq import (baca_soal_pdf, proses_file_zip_realtime)

# Load environment variables dari file .env
load_dotenv()

# --- Konfigurasi Halaman ---
st.set_page_config(
    page_title="Asisten Penilai Kode Otomatis (Groq)",
    page_icon="⚡",
    layout="wide"
)

# --- UI Sidebar untuk Konfigurasi ---
st.sidebar.header("⚙️ Konfigurasi")

# Cek apakah API key ada di environment variable
env_api_key = os.getenv('GROQ_API_KEY')
env_model = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
env_temperature = float(os.getenv('GROQ_TEMPERATURE', '0.1'))

# Tampilkan status API key
if env_api_key:
    st.sidebar.success("✅ API Key terdeteksi dari file .env")
    # Tampilkan sebagian API key untuk konfirmasi (masked)
    masked_key = env_api_key[:8] + "..." + env_api_key[-4:] if len(env_api_key) > 12 else "***"
    st.sidebar.caption(f"API Key: {masked_key}")
    
    # Opsi untuk override API key
    use_custom_key = st.sidebar.checkbox("Gunakan API Key berbeda", value=False)
    if use_custom_key:
        api_key = st.sidebar.text_input("API Key Groq alternatif:", type="password")
        if not api_key:
            api_key = env_api_key
    else:
        api_key = env_api_key
else:
    st.sidebar.warning("⚠️ API Key tidak ditemukan di file .env")
    st.sidebar.info("Buat file `.env` di root project dan tambahkan:\n```\nGROQ_API_KEY=your_key_here\n```")
    api_key = st.sidebar.text_input("Masukkan API Key Groq:", type="password")

# Opsi model
st.sidebar.subheader("Model Settings")
available_models = [
    "llama-3.3-70b-versatile",
    "llama-3.2-90b-text-preview",
    "llama-3.1-70b-versatile",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
    "gemma-7b-it"
]
selected_model = st.sidebar.selectbox(
    "Pilih Model:",
    available_models,
    index=available_models.index(env_model) if env_model in available_models else 0
)

# Temperature setting
temperature = st.sidebar.slider(
    "Temperature (0=konsisten, 1=kreatif):",
    min_value=0.0,
    max_value=1.0,
    value=env_temperature,
    step=0.1
)

st.sidebar.markdown("---")
st.sidebar.markdown("📚 [Dokumentasi Groq](https://console.groq.com/docs)")
st.sidebar.markdown("🔑 [Dapatkan API Key](https://console.groq.com/keys)")

# --- Judul Utama ---
st.title("⚡ Asisten Penilai Kode Otomatis")
st.markdown("Didukung oleh **Groq** untuk penilaian super cepat.")

# --- Layout Utama dengan Kolom ---
col1, col2 = st.columns([1, 1.5])

# --- Kolom 1: Input Pengguna ---
with col1:
    st.header("1. Masukkan Soal & Kriteria")

    input_method = st.radio("Pilih metode input soal:", ("Input Teks Langsung", "Unggah File PDF"))
    
    soal_text = ""
    if input_method == "Input Teks Langsung":
        soal_text = st.text_area("Masukkan teks soal di sini:", height=200, placeholder="Contoh: Buatlah program Python untuk menghitung faktorial...")
    else:
        uploaded_pdf = st.file_uploader("Pilih file soal (.pdf)", type="pdf")
        if uploaded_pdf:
            soal_text = baca_soal_pdf(uploaded_pdf.getvalue())
            st.success("File PDF berhasil dibaca!")
            with st.expander("Lihat teks dari PDF"):
                st.write(soal_text)

    kriteria_text = st.text_area(
        "Kriteria Penilaian Tambahan (Opsional)", 
        height=150, 
        placeholder="Contoh:\n- Gunakan fungsi rekursif (wajib)\n- Kode harus memiliki komentar"
    )

    st.header("2. Unggah File Tugas")
    uploaded_zip = st.file_uploader(
        "Unggah file .zip yang berisi semua tugas",
        type="zip"
    )

    mulai_button = st.button("🚀 Mulai Penilaian", type="primary", use_container_width=True)

# --- Kolom 2: Output Hasil ---
with col2:
    st.header("Hasil Penilaian")
    
    # Container untuk progress dan tabel
    progress_container = st.container()
    table_container = st.container()
    download_container = st.container()

    if mulai_button:
        if not api_key:
            st.error("Kunci API Groq wajib diisi di sidebar kiri.")
        elif not soal_text:
            st.error("Soal tidak boleh kosong. Silakan isi teks soal atau unggah PDF.")
        elif not uploaded_zip:
            st.error("File .zip tugas belum diunggah.")
        else:
            try:
                # --- PERUBAHAN UTAMA: INISIALISASI CLIENT GROQ ---
                client = Groq(api_key=api_key)
                
                # Placeholder untuk progress bar dan status
                with progress_container:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                # Placeholder untuk tabel
                with table_container:
                    table_placeholder = st.empty()
                    
                # List untuk menyimpan hasil
                hasil_list = []
                
                # Generator untuk proses real-time dengan model dan temperature dari settings
                for progress_info in proses_file_zip_realtime(
                    client=client,
                    zip_file_bytes=uploaded_zip.getvalue(),
                    soal_text=soal_text,
                    kriteria_text=kriteria_text,
                    model=selected_model,
                    temperature=temperature
                ):
                    if progress_info['type'] == 'progress':
                        # Update progress bar dan status
                        progress = progress_info['current'] / progress_info['total']
                        progress_bar.progress(progress)
                        status_text.text(f"Memproses file {progress_info['current']}/{progress_info['total']}: {progress_info['file_name']}...")
                        
                    elif progress_info['type'] == 'result':
                        # Tambahkan hasil ke list
                        hasil_list.append(progress_info['data'])
                        
                        # Update tabel dengan hasil terbaru
                        df_hasil = pd.DataFrame(hasil_list)
                        
                        # Styling untuk tabel
                        def style_dataframe(df):
                            def color_nilai(val):
                                if isinstance(val, (int, float)):
                                    if val >= 85:
                                        return 'background-color: #d4edda; color: #155724'
                                    elif val >= 70:
                                        return 'background-color: #fff3cd; color: #856404'
                                    elif val >= 50:
                                        return 'background-color: #f8d7da; color: #721c24'
                                    else:
                                        return 'background-color: #f5c6cb; color: #721c24'
                                return ''
                            
                            return df.style.applymap(color_nilai, subset=['nilai'])
                        
                        # Tampilkan tabel dengan styling
                        table_placeholder.dataframe(
                            style_dataframe(df_hasil),
                            use_container_width=True,
                            hide_index=True
                        )
                    
                    elif progress_info['type'] == 'error':
                        st.error(f"Error: {progress_info['message']}")
                
                # Selesai - update progress dan status
                progress_bar.progress(1.0)
                status_text.success("✅ Semua file telah selesai dinilai!")
                
                # Tampilkan tombol download jika ada hasil
                if hasil_list:
                    with download_container:
                        st.markdown("---")
                        
                        # Tampilkan statistik
                        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                        df_final = pd.DataFrame(hasil_list)
                        
                        with col_stat1:
                            st.metric("Total File", len(hasil_list))
                        with col_stat2:
                            st.metric("Rata-rata Nilai", f"{df_final['nilai'].mean():.1f}")
                        with col_stat3:
                            st.metric("Nilai Tertinggi", df_final['nilai'].max())
                        with col_stat4:
                            st.metric("Nilai Terendah", df_final['nilai'].min())
                        
                        # Buat file Excel untuk download
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df_final.to_excel(writer, index=False, sheet_name='Hasil Penilaian')
                            
                            # Auto-adjust columns width
                            worksheet = writer.sheets['Hasil Penilaian']
                            for column in df_final:
                                column_length = max(df_final[column].astype(str).map(len).max(), len(column))
                                col_idx = df_final.columns.get_loc(column)
                                worksheet.column_dimensions[chr(65 + col_idx)].width = column_length + 2
                                
                        excel_data = output.getvalue()

                        st.download_button(
                            label="📥 Unduh Hasil sebagai Excel (.xlsx)",
                            data=excel_data,
                            file_name="HasilPenilaian_Groq.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                        )
                else:
                    st.warning("Tidak ada hasil untuk ditampilkan.")

            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")