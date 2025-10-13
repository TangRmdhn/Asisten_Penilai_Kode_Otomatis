# penilai_otomatis.py
# File ini berisi semua fungsi inti untuk proses penilaian otomatis.

import io
import json
import re
import time
import zipfile
from typing import Dict, List, Optional, Any, Generator

import pandas as pd
from groq import Groq
from pypdf import PdfReader


def baca_soal_pdf(file_bytes: bytes) -> str:
    """Membaca teks dari file PDF yang diupload."""
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        full_text = "".join(page.extract_text() for page in reader.pages)
        return full_text
    except Exception as e:
        print(f"Error saat membaca PDF: {e}")
        return ""

def buat_prompt_penilaian(soal_text: str, kriteria_text: str) -> str:
    """Membuat system prompt dinamis berdasarkan soal dan kriteria."""
    kriteria_section = ""
    if kriteria_text:
        kriteria_section = f"""
Kriteria Penilaian Tambahan
{kriteria_text}
"""
    prompt = f"""
Anda adalah seorang asisten penilai kode pemrograman yang ahli, teliti, dan objektif. Tugas Anda adalah menganalisis kode yang diberikan, membandingkannya dengan soal, dan memberikan penilaian serta umpan balik (feedback).

Soal:
{soal_text}
{kriteria_section}
Aturan Penting
1. Sistem Penilaian: Penilaian berawal dari nilai 100 yang selalu dikurang ketika ada kesalahan.
1.  Akurasi Logika: Pastikan kode berfungsi sesuai permintaan soal. Nilai berkurang besar jika terdapat kesalahan logika.
2.  Fokus pada Kesalahan: Fokus mencari kesalahan. Jika terdapat kesalahan fatal yang tidak mengikuti alur perintah soal maka pengurangan cukup besar. Jika program mengikuti alur tapi kesalah simpel, maka hanya penguranan nilai sedikit.
3.  Penanganan Error: Cek apakah ada penanganan untuk input yang tidak valid (pengurangan nilai kecil).

Format Output WAJIB
Hasil penilaian HARUS diberikan dalam format JSON yang valid dengan struktur sebagai berikut. JANGAN tambahkan teks atau penjelasan lain di luar blok JSON.

{{
  "nama_file": "[nama file yang dinilai]",
  "nilai": [nilai akhir dalam format ANGKA 0-100, bukan string],
  "kesalahan": "[kesalahan yang terdapat pada program (jika ada salah)]"
  "feedback": "[feedback singkat, jelas, dan konstruktif mengenai penilaian (jika ada salah) maksimal 3 kalimat]"
}}
"""
    return prompt.strip()

def bersihkan_json(text: str) -> Optional[str]:
    """
    Membersihkan teks output dari LLM untuk mendapatkan string JSON yang valid.
    Fungsi ini akan mencari blok JSON yang diapit oleh ```json ... ``` atau langsung oleh { ... }.
    """
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    return None

def dapatkan_penilaian(
    client: Groq, 
    system_prompt: str, 
    nama_file: str, 
    kode: str,
    model: str = "llama-3.3-70b-versatile",
    temperature: float = 0.1
) -> Dict[str, Any]:
    """Memanggil API Groq untuk mendapatkan penilaian dan memastikan outputnya adalah JSON valid."""
    max_retries = 3
    retry_count = 0
    raw_output = ""
    
    while retry_count < max_retries:
        try:
            user_content = f"Nama File: {nama_file}\n\nKode Program:\n```\n{kode}\n```"
            
            completion = client.chat.completions.create(
                model=model,  # Menggunakan model dari parameter
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=temperature,  # Menggunakan temperature dari parameter
                max_tokens=1024,
            )
            
            raw_output = completion.choices[0].message.content
            
            json_string = bersihkan_json(raw_output)
            
            if not json_string:
                raise json.JSONDecodeError("Blok JSON tidak ditemukan.", raw_output, 0)

            parsed_json = json.loads(json_string)
            
            if not all(k in parsed_json for k in ["nama_file", "nilai", "kesalahan", "feedback"]):
                 raise ValueError("JSON tidak memiliki field yang dibutuhkan.")
            if not isinstance(parsed_json["nilai"], int):
                try:
                    parsed_json["nilai"] = int(parsed_json["nilai"])
                except (ValueError, TypeError):
                    raise TypeError("Field 'nilai' harus berupa angka (integer).")
            
            return parsed_json

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            retry_count += 1
            print(f"Percobaan {retry_count}/{max_retries}: Gagal mem-parsing JSON untuk {nama_file}. Error: {e}")
            if retry_count >= max_retries:
                return {
                    "nama_file": nama_file,
                    "nilai": 0,
                    "kesalahan": "GAGAL proses",
                    "feedback": f"GAGAL DIPROSES: Output dari AI bukan JSON yang valid setelah {max_retries} percobaan. Output mentah: {raw_output[:200]}..."
                }
            time.sleep(2)
    return {}

def proses_file_zip_realtime(
    client: Groq, 
    zip_file_bytes: bytes, 
    soal_text: str, 
    kriteria_text: str,
    model: str = "llama-3.3-70b-versatile",
    temperature: float = 0.1
) -> Generator[Dict[str, Any], None, None]:
    """
    Mengekstrak file dari zip, menilai satu per satu, dan yield hasilnya secara real-time.
    
    Args:
        client: Groq client instance
        zip_file_bytes: Bytes dari file ZIP
        soal_text: Teks soal
        kriteria_text: Kriteria penilaian tambahan
        model: Model Groq yang akan digunakan
        temperature: Temperature untuk model (0-1)
    
    Yields:
        Dict dengan format:
        - {'type': 'progress', 'current': int, 'total': int, 'file_name': str} untuk update progress
        - {'type': 'result', 'data': dict} untuk hasil penilaian
        - {'type': 'error', 'message': str} untuk error
    """
    system_prompt = buat_prompt_penilaian(soal_text, kriteria_text)

    try:
        with zipfile.ZipFile(io.BytesIO(zip_file_bytes), 'r') as zip_ref:
            # Filter file yang valid (bukan folder dan bukan __MACOSX)
            file_list = [f for f in zip_ref.namelist() if not f.endswith('/') and not f.startswith('__MACOSX')]
            total_files = len(file_list)
            
            for i, file_name in enumerate(file_list, 1):
                # Yield progress info
                yield {
                    'type': 'progress',
                    'current': i,
                    'total': total_files,
                    'file_name': file_name
                }
                
                try:
                    with zip_ref.open(file_name) as file:
                        try:
                            kode_program = file.read().decode('utf-8')
                        except UnicodeDecodeError:
                            file.seek(0)
                            kode_program = file.read().decode('latin-1', errors='ignore')

                except Exception as e:
                    print(f"Gagal membaca file {file_name} dari zip: {e}")
                    hasil = {
                        "nama_file": file_name,
                        "nilai": 0,
                        "kesalahan": "GAGAL proses",
                        "feedback": f"ERROR: Tidak dapat membaca file. Mungkin file corrupt atau format tidak didukung."
                    }
                    # Yield hasil error
                    yield {'type': 'result', 'data': hasil}
                    continue

                # Proses penilaian dengan model dan temperature yang diberikan
                hasil = dapatkan_penilaian(
                    client, 
                    system_prompt, 
                    file_name, 
                    kode_program,
                    model=model,
                    temperature=temperature
                )
                
                # Yield hasil penilaian
                yield {'type': 'result', 'data': hasil}
                
    except zipfile.BadZipFile:
        yield {
            'type': 'error',
            'message': "File yang diupload bukan format .zip yang valid."
        }
    except Exception as e:
        yield {
            'type': 'error',
            'message': f"Terjadi error tak terduga: {e}"
        }


# Fungsi lama untuk backward compatibility (opsional, bisa dihapus jika tidak diperlukan)
def proses_file_zip(
    client: Groq, 
    zip_file_bytes: bytes, 
    soal_text: str, 
    kriteria_text: str,
    progress_indicator: Any
) -> List[Dict[str, Any]]:
    """
    Fungsi lama untuk backward compatibility.
    Mengekstrak file dari zip, menilai satu per satu, dan mengembalikan hasilnya.
    """
    hasil_penilaian = []
    
    for progress_info in proses_file_zip_realtime(client, zip_file_bytes, soal_text, kriteria_text):
        if progress_info['type'] == 'progress':
            progress_indicator.text(f"Memproses file {progress_info['current']}/{progress_info['total']}: {progress_info['file_name']}...")
        elif progress_info['type'] == 'result':
            hasil_penilaian.append(progress_info['data'])
        elif progress_info['type'] == 'error':
            return [{"nama_file": "error", "nilai": 0, "kesalahan": "GAGAL proses", "feedback": progress_info['message']}]
    
    return hasil_penilaian