# ⚡ Asisten Penilai Kode Otomatis

Aplikasi web untuk menilai tugas pemrograman secara otomatis menggunakan AI dari **Groq**. Sistem ini dapat membaca soal dari PDF atau teks, kemudian menilai *batch* file kode (dalam `.zip`) dan memberikan *feedback* mendetail beserta skor untuk setiap file.

<br>

## ✨ Fitur Utama

  - 🤖 **Penilaian AI Otomatis**: Menggunakan model LLM super cepat dari Groq untuk penilaian yang akurat dan konsisten.
  - 📄 **Dukungan PDF & Teks**: Baca soal langsung dari file `.pdf` atau salin-tempel teks soal.
  - 📦 **Batch Processing**: Nilai puluhan atau ratusan file tugas sekaligus hanya dengan satu file `.zip`.
  - ⚡ **Real-time Progress**: Lihat progres penilaian dan hasil yang masuk satu per satu secara *live*.
  - 📊 **Statistik & Visualisasi**: Dapatkan ringkasan statistik (rata-rata, tertinggi, terendah) dan tabel hasil berkode warna.
  - 📤 **Ekspor Hasil**: Unduh laporan penilaian lengkap dalam format `.xlsx` (Excel) atau `.csv`.
  - 🔧 **Konfigurasi Model**: Pilih model Groq yang paling sesuai dengan kebutuhan Anda, dari yang tercepat hingga yang paling akurat.

## 🚀 Instalasi & Setup

Ini adalah panduan lengkap untuk menjalankan aplikasi di komputer lokal Anda.

### Prasyarat

  - **Python 3.8** atau versi lebih baru.
  - **API Key Groq**: Anda bisa mendapatkannya secara gratis di [Groq Console](https://console.groq.com/keys).

-----

### Langkah 1: Clone Repository

Buka terminal atau Command Prompt, lalu *clone* repository ini ke komputer Anda dan masuk ke direktorinya.

```bash
git clone https://github.com/username/asisten-penilai-kode.git
cd asisten-penilai-kode
```

*(Ganti `username/asisten-penilai-kode` dengan URL repository Anda yang sebenarnya)*

### Langkah 2: Buat Virtual Environment (Sangat Direkomendasikan)

Membuat *virtual environment* (venv) adalah *best practice* untuk mengisolasi *dependency* project Anda.

```bash
# Buat venv di folder bernama 'venv'
python -m venv venv
```

Selanjutnya, aktifkan venv tersebut:

  - **Windows (Command Prompt):**
    ```bash
    venv\Scripts\activate
    ```
  - **macOS / Linux (Bash):**
    ```bash
    source venv/bin/activate
    ```

Anda akan melihat `(venv)` di awal baris terminal jika berhasil.

### Langkah 3: Install Dependencies

Pastikan venv Anda aktif, lalu install semua *library* yang dibutuhkan dari `requirements.txt`.

```bash
pip install -r requirements.txt
```

### Langkah 4: Konfigurasi API Key

Aplikasi ini membaca API Key dari file `.env`.

1.  Buat file baru bernama `.env` di dalam folder utama project (di lokasi yang sama dengan `app.py`).
2.  Buka file `.env` tersebut dengan teks editor dan tambahkan baris berikut:

<!-- end list -->

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Ganti `gsk_xxxxxxxx...` dengan API Key Groq yang sudah Anda dapatkan dari [Groq Console](https://console.groq.com/keys).

## 💻 Menjalankan Aplikasi

Setelah semua setup selesai, jalankan aplikasi menggunakan Streamlit:

```bash
streamlit run app.py
```

Aplikasi akan otomatis terbuka di browser Anda (biasanya di `http://localhost:8501`).

## 📖 Cara Penggunaan

1.  **Input Soal**: Di sisi kiri, pilih tab "Input Teks" untuk mengetik soal, atau "Upload PDF" untuk mengunggah file soal.
2.  **Kriteria Tambahan (Opsional)**: Masukkan poin-poin penting yang harus dinilai oleh AI (contoh: "Wajib menggunakan rekursif", "Nama variabel harus jelas").
3.  **Upload File Tugas**: Kompres semua file kode siswa (misal: `Ahmad.py`, `Budi.py`) ke dalam **satu file .zip** lalu unggah file ZIP tersebut.
4.  **Pilih Model (Opsional)**: Di sidebar kiri, Anda bisa memilih model AI yang ingin digunakan.
5.  **Mulai Penilaian**: Klik tombol **"🚀 Mulai Penilaian"**.
6.  **Lihat Hasil**: Hasil akan muncul satu per satu di tabel sebelah kanan secara *real-time*. Tabel akan diberi kode warna untuk memudahkan analisis.
7.  **Download Laporan**: Setelah selesai, statistik penilaian akan muncul. Gunakan tombol "Download Excel" atau "Download CSV" untuk menyimpan laporan.

**Struktur `.zip` yang Disarankan:**

```
tugas_mahasiswa.zip
├── 2024001_Ahmad.py
├── 2024002_Budi.py
├── SubFolder/2024003_Citra.py  <-- (Aplikasi bisa membaca file di dalam sub-folder)
└── ...
```

## ⚙️ Konfigurasi Lanjutan

### Pilihan Model

Anda dapat memilih model yang berbeda di sidebar. Setiap model memiliki kelebihan:

| Model | Keterangan |
| :--- | :--- |
| `openai/gpt-oss-120b` | ✅ **Default & Recommended**. Model terbesar & terbaik untuk akurasi tinggi. |
| `llama-3.3-70b-versatile` | ⚡ Model cepat dengan performa bagus. |
| `llama-3.2-90b-text-preview` | 🔬 Model eksperimental dengan 90B parameter. |
| `llama-3.1-70b-versatile` | 💪 Model stabil untuk berbagai tugas. |
| `mixtral-8x7b-32768` | 🎯 Model MoE dengan konteks panjang (cocok untuk kode yang sangat panjang). |
| `gemma2-9b-it` | 💎 Model ringan dari Google, sangat cepat. |
| `gemma-7b-it` | ⚡ Model paling ringan & tercepat (cocok untuk *batch* sangat besar). |

### Temperature

Saat ini, `temperature` diatur statis ke **`0.1`** di dalam `app.py`. Nilai yang rendah ini dipilih untuk memastikan AI memberikan penilaian yang konsisten, objektif, dan tidak terlalu "kreatif" antar file.

## 📁 Struktur Project

```
asisten-penilai-kode/
│
├── .devcontainer/              # Konfigurasi untuk VS Code Dev Containers
├── .streamlit/               # Konfigurasi Streamlit (jika ada)
├── venv/                       # Folder virtual environment (setelah setup)
│
├── app.py                      # File utama (UI Streamlit)
├── penilai_otomatis.py         # Logika inti (backend) penilaian & Groq API
├── requirements.txt            # Daftar dependency Python
├── .env                        # File konfigurasi API key (perlu dibuat manual)
├── .gitignore                  # File yang diabaikan oleh Git
└── README.md                   # Dokumentasi ini
```

## 🔧 Troubleshooting

  - **Error: "API Key tidak valid"**

      - Pastikan file `.env` sudah benar-benar bernama `.env` (bukan `.env.txt`).
      - Pastikan file `.env` ada di *root directory* (sejajar dengan `app.py`).
      - Pastikan API Key di-salin dengan benar tanpa spasi tambahan.
      - **Restart aplikasi** setelah mengubah `.env`.

  - **Error: "File ZIP tidak valid"**

      - Pastikan file yang di-upload adalah `.zip`. Format `.rar`, `.7z`, dll. **tidak didukung**.
      - Coba buat ulang file `.zip` dengan *tool* kompresi standar (bawaan Windows/macOS, 7-Zip).

  - **Error: "Cannot decode file"**

      - Ini berarti ada file kode di dalam ZIP yang tidak menggunakan encoding standar (seperti UTF-8).
      - Aplikasi akan mencoba membacanya sebagai `latin-1`, namun jika tetap gagal, file tersebut akan diberi nilai 0 dengan *feedback* error.

## 🤝 Berkontribusi

Kontribusi sangat diterima\! Jika Anda ingin mengembangkan fitur baru atau memperbaiki bug:

1.  *Fork* repository ini.
2.  Buat *branch* baru (`git checkout -b feature/FiturKeren`).
3.  *Commit* perubahan Anda (`git commit -m 'Menambahkan FiturKeren'`).
4.  *Push* ke branch (`git push origin feature/FiturKeren`).
5.  Buat *Pull Request*.

## 👨‍💻 Author

**Bintang Ramadhan**

  - GitHub: [@TangRmdhn](https://github.com/TangRmdhn)
  - Email: bintangramadhan0710@gmal.com

## 🙏 Acknowledgments

  - **[Groq](https://groq.com/)** untuk platform inferensi AI yang luar biasa cepat.
  - **[Streamlit](https://streamlit.io/)** untuk *framework* aplikasi web Python yang simpel dan keren.
  - **[Meta AI](https://ai.meta.com/llama/)** & **[Google](https://www.google.com/search?q=https://ai.google/gemma/)** untuk model-model *open-source* yang powerful.

-----

⭐ Jika project ini membantu Anda, jangan ragu untuk memberikan *star* di GitHub\!