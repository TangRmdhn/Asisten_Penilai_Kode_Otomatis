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
from penilai_otomatis import (baca_soal_pdf, proses_file_zip_realtime)

# Load environment variables dari file .env
load_dotenv()

# --- Konfigurasi Halaman ---
st.set_page_config(
    page_title="Asisten Penilai Kode Otomatis (Groq)",
    page_icon="⚡",
    layout="wide"
)

# --- Cek API Key dari Environment ---
api_key = os.getenv('GROQ_API_KEY')
if not api_key:
    st.error("❌ **API Key tidak ditemukan!**")
    st.info("""
    ### Setup API Key:
    1. Buat file `.env` di root project
    2. Tambahkan baris berikut:
    ```
    GROQ_API_KEY=your_groq_api_key_here
    ```
    3. Dapatkan API key di [Groq Console](https://console.groq.com/keys)
    4. Restart aplikasi setelah menambahkan API key
    """)
    st.stop()

# --- Temperature Static ---
TEMPERATURE = 0.1  # Temperature rendah untuk konsistensi penilaian

# --- UI Sidebar untuk Model Selection ---
st.sidebar.header("⚙️ Konfigurasi Model")

# Daftar model yang tersedia
available_models = [
    "openai/gpt-oss-120b",  # Model default
    "llama-3.3-70b-versatile",
    "llama-3.2-90b-text-preview", 
    "llama-3.1-70b-versatile",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
    "gemma-7b-it"
]

# Dropdown pemilihan model dengan GPT OSS 120B sebagai default
selected_model = st.sidebar.selectbox(
    "Pilih Model AI:",
    available_models,
    index=0,  # Index 0 = openai/gpt-oss-120b
    help="Model GPT OSS 120B direkomendasikan untuk hasil terbaik"
)

# Info model yang dipilih
model_info = {
    "openai/gpt-oss-120b": "🚀 Model terbesar & terbaik untuk akurasi tinggi",
    "llama-3.3-70b-versatile": "⚡ Model cepat dengan performa bagus",
    "llama-3.2-90b-text-preview": "🔬 Model eksperimental dengan 90B parameter",
    "llama-3.1-70b-versatile": "💪 Model stabil untuk berbagai tugas",
    "mixtral-8x7b-32768": "🎯 Model MoE dengan konteks panjang",
    "gemma2-9b-it": "💎 Model ringan dari Google",
    "gemma-7b-it": "⚡ Model paling ringan & cepat"
}

if selected_model in model_info:
    st.sidebar.info(model_info[selected_model])

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Status Sistem")
st.sidebar.success("✅ API Key terdeteksi")
st.sidebar.caption(f"🤖 Model: **{selected_model.split('/')[-1]}**")
st.sidebar.caption(f"🌡️ Temperature: **{TEMPERATURE}** (static)")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📚 Resources")
st.sidebar.markdown("[Dokumentasi Groq](https://console.groq.com/docs)")
st.sidebar.markdown("[Model Benchmark](https://console.groq.com/models)")

# --- Judul Utama ---
st.title("⚡ Asisten Penilai Kode Otomatis")
st.markdown("Langkah-langkah Penggunaan :")
st.markdown("1. Upload soal, bisa berupa teks atau upload pdf\n2. Tambahkan Kriteria Penilaian (Opsional)\n3. Upload kumpulan file jawaban yang masukan ke .zip")

# --- Layout Utama dengan Kolom ---
col1, col2 = st.columns([1, 1.5])

# --- Kolom 1: Input Pengguna ---
with col1:
    st.header("📝 Input Soal & Tugas")
    
    # Tab untuk metode input
    tab1, tab2 = st.tabs(["✏️ Input Teks", "📄 Upload PDF"])
    
    soal_text = ""
    with tab1:
        soal_text = st.text_area(
            "Masukkan teks soal:", 
            height=250, 
            placeholder="Contoh:\nBuatlah program Python untuk menghitung faktorial dari sebuah bilangan.\nProgram harus menggunakan fungsi rekursif..."
        )
    
    with tab2:
        uploaded_pdf = st.file_uploader("Pilih file soal (.pdf)", type="pdf")
        if uploaded_pdf:
            soal_text = baca_soal_pdf(uploaded_pdf.getvalue())
            st.success("✅ File PDF berhasil dibaca!")
            with st.expander("Lihat teks dari PDF"):
                st.write(soal_text)

    st.markdown("---")
    
    kriteria_text = st.text_area(
        "📋 Kriteria Penilaian Tambahan (Opsional)", 
        height=120, 
        placeholder="Contoh:\n• Gunakan fungsi rekursif (wajib)\n• Kode harus memiliki komentar\n• Implementasi error handling",
        help="Tambahkan kriteria khusus untuk penilaian jika diperlukan"
    )

    st.markdown("---")
    
    st.subheader("📦 Upload File Tugas")
    uploaded_zip = st.file_uploader(
        "Pilih file .zip yang berisi semua tugas",
        type="zip",
        help="File ZIP harus berisi file-file kode program (Python, Java, C++, dll)"
    )
    
    if uploaded_zip:
        st.success(f"✅ File uploaded: {uploaded_zip.name}")

    # Tombol mulai penilaian
    mulai_button = st.button(
        "🚀 Mulai Penilaian", 
        type="primary", 
        use_container_width=True,
        disabled=not (soal_text and uploaded_zip)
    )

# --- Kolom 2: Output Hasil ---
with col2:
    st.header("📊 Hasil Penilaian")
    
    # Container untuk progress dan tabel
    progress_container = st.container()
    table_container = st.container()
    download_container = st.container()
    
    # Info default
    if not mulai_button:
        with table_container:
            st.info("💡 Hasil penilaian akan muncul di sini secara real-time setelah Anda klik 'Mulai Penilaian'")
            
            # Panduan singkat
            with st.expander("📖 Cara Penggunaan"):
                st.markdown("""
                1. **Input Soal**: Ketik langsung atau upload PDF
                2. **Kriteria Tambahan**: Opsional, untuk penilaian lebih spesifik
                3. **Upload Tugas**: File ZIP berisi semua file kode
                4. **Klik Mulai**: Tunggu hasil muncul satu per satu
                5. **Download Excel**: Setelah selesai, unduh hasil lengkap
                """)

    if mulai_button:
        if not soal_text:
            st.error("❌ Soal tidak boleh kosong. Silakan isi teks soal atau upload PDF.")
        elif not uploaded_zip:
            st.error("❌ File .zip tugas belum di-upload.")
        else:
            try:
                # Inisialisasi Groq client
                client = Groq(api_key=api_key)
                
                # Placeholder untuk progress bar dan status
                with progress_container:
                    st.markdown(f"**Model:** {selected_model} | **Temperature:** {TEMPERATURE}")
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    elapsed_time = st.empty()
                    
                # Placeholder untuk tabel
                with table_container:
                    table_placeholder = st.empty()
                    
                # List untuk menyimpan hasil
                hasil_list = []
                
                # Timer
                import time
                start_time = time.time()
                
                # Generator untuk proses real-time
                for progress_info in proses_file_zip_realtime(
                    client=client,
                    zip_file_bytes=uploaded_zip.getvalue(),
                    soal_text=soal_text,
                    kriteria_text=kriteria_text,
                    model=selected_model,
                    temperature=TEMPERATURE
                ):
                    if progress_info['type'] == 'progress':
                        # Update progress bar dan status
                        progress = progress_info['current'] / progress_info['total']
                        progress_bar.progress(progress)
                        status_text.text(f"⏳ Memproses file {progress_info['current']}/{progress_info['total']}: {progress_info['file_name']}...")
                        
                        # Update elapsed time
                        elapsed = time.time() - start_time
                        elapsed_time.caption(f"⏱️ Waktu: {elapsed:.1f} detik")
                        
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
                                        return 'background-color: #d4edda; color: #155724; font-weight: bold'
                                    elif val >= 70:
                                        return 'background-color: #fff3cd; color: #856404'
                                    elif val >= 50:
                                        return 'background-color: #f8d7da; color: #721c24'
                                    else:
                                        return 'background-color: #f5c6cb; color: #721c24; font-weight: bold'
                                return ''
                            
                            return df.style.applymap(color_nilai, subset=['nilai'])
                        
                        # Tampilkan tabel dengan styling
                        table_placeholder.dataframe(
                            style_dataframe(df_hasil),
                            use_container_width=True,
                            hide_index=True,
                            height=400  # Fixed height untuk scrollable table
                        )
                    
                    elif progress_info['type'] == 'error':
                        st.error(f"❌ Error: {progress_info['message']}")
                
                # Selesai - update progress dan status
                progress_bar.progress(1.0)
                total_time = time.time() - start_time
                status_text.success(f"✅ Semua file telah selesai dinilai!")
                elapsed_time.caption(f"⏱️ Total waktu: {total_time:.1f} detik ({total_time/len(hasil_list):.1f} detik/file)")
                
                # Tampilkan tombol download jika ada hasil
                if hasil_list:
                    with download_container:
                        st.markdown("---")
                        
                        # Tampilkan statistik dalam cards
                        st.subheader("📈 Statistik Penilaian")
                        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                        df_final = pd.DataFrame(hasil_list)
                        
                        with col_stat1:
                            st.metric(
                                "📁 Total File", 
                                len(hasil_list),
                                help="Jumlah file yang dinilai"
                            )
                        with col_stat2:
                            avg_nilai = df_final['nilai'].mean()
                            st.metric(
                                "📊 Rata-rata", 
                                f"{avg_nilai:.1f}",
                                delta=f"{avg_nilai-70:.1f} dari 70",
                                delta_color="normal" if avg_nilai >= 70 else "inverse",
                                help="Nilai rata-rata semua tugas"
                            )
                        with col_stat3:
                            st.metric(
                                "🏆 Tertinggi", 
                                df_final['nilai'].max(),
                                help="Nilai tertinggi"
                            )
                        with col_stat4:
                            st.metric(
                                "📉 Terendah", 
                                df_final['nilai'].min(),
                                help="Nilai terendah"
                            )
                        
                        # Distribusi nilai
                        st.subheader("📊 Distribusi Nilai")
                        nilai_ranges = {
                            "A (85-100)": len(df_final[df_final['nilai'] >= 85]),
                            "B (70-84)": len(df_final[(df_final['nilai'] >= 70) & (df_final['nilai'] < 85)]),
                            "C (50-69)": len(df_final[(df_final['nilai'] >= 50) & (df_final['nilai'] < 70)]),
                            "D (< 50)": len(df_final[df_final['nilai'] < 50])
                        }
                        
                        dist_cols = st.columns(4)
                        for idx, (grade, count) in enumerate(nilai_ranges.items()):
                            with dist_cols[idx]:
                                st.metric(grade, count)
                        
                        # Buat file Excel untuk download
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df_final.to_excel(writer, index=False, sheet_name='Hasil Penilaian')
                            
                            # Auto-adjust columns width
                            worksheet = writer.sheets['Hasil Penilaian']
                            for column in df_final:
                                column_length = max(df_final[column].astype(str).map(len).max(), len(column))
                                col_idx = df_final.columns.get_loc(column)
                                worksheet.column_dimensions[chr(65 + col_idx)].width = min(column_length + 2, 50)
                                
                        excel_data = output.getvalue()

                        # Tombol download
                        st.markdown("---")
                        col_dl1, col_dl2 = st.columns(2)
                        with col_dl1:
                            st.download_button(
                                label="📥 Download Excel (.xlsx)",
                                data=excel_data,
                                file_name=f"HasilPenilaian_{selected_model.split('/')[-1]}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True,
                            )
                        with col_dl2:
                            # Download as CSV
                            csv_data = df_final.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Download CSV",
                                data=csv_data,
                                file_name=f"HasilPenilaian_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                use_container_width=True,
                            )
                else:
                    st.warning("⚠️ Tidak ada hasil untuk ditampilkan.")

            except Exception as e:
                st.error(f"❌ Terjadi kesalahan: {e}")
                st.info("💡 Pastikan API key di file .env sudah benar dan model yang dipilih tersedia.")