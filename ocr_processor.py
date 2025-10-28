import os
import threading
from pdf2image import convert_from_path
from PIL import Image
import easyocr
import numpy as np
from config import Config
from utils import load_dataset
import re

# Inisialisasi EasyOCR (Indonesia + Inggris)
reader = easyocr.Reader(['id', 'en'], gpu=False)


def process_file(file_path, filename):
    """Menentukan apakah file PDF atau gambar, lalu proses OCR"""
    if filename.lower().endswith(".pdf"):
        text = process_pdf(file_path)
    else:
        text = process_image(file_path)

    # Format hasil agar rapi
    formatted = format_ocr_text(text)
    return formatted


def process_pdf(file_path):
    """Konversi PDF ke teks menggunakan EasyOCR"""
    pages = convert_from_path(file_path, poppler_path=Config.POPPLER_PATH)
    texts = []
    for page in pages:
        np_img = np.array(page)
        result = reader.readtext(np_img, detail=0)
        texts.append("\n".join(result))
    return "\n\n".join(texts)


def process_image(file_path):
    """OCR untuk gambar tunggal"""
    print(f"🖼️ Mendeteksi file gambar: {file_path}")
    image = np.array(Image.open(file_path))
    result = reader.readtext(image, detail=0)
    return "\n".join(result)


# ==========================================================
# 🧹 FORMAT HASIL OCR AGAR RAPI
# ==========================================================
def format_ocr_text(raw_text: str) -> str:
    """
    Membersihkan hasil OCR:
    - Hilangkan spasi dan baris berlebihan
    - Gabungkan kata yang terpecah
    - Tambahkan newline pada bagian penting surat
    """
    if not raw_text:
        return ""

    text = raw_text.strip()

    # Hilangkan spasi ganda dan baris kosong
    text = re.sub(r'\s+', ' ', text)

    # Tambahkan baris baru setelah kata kunci penting (agar menyerupai surat)
    keywords = [
        "SURAT", "KETERANGAN", "IZIN", "SAKIT",
        "Kepada", "Yth", "Nama", "Nim", "Prodi", "Kelas",
        "Dengan ini", "mohon", "tidak mengikuti",
        "tanggal", "karena", "Demikian", "Mengetahui",
        "PA", "WALI", "ORTU", "Nip", "Note", "Lhokseumawe"
    ]

    for kw in keywords:
        text = re.sub(fr'({kw})', r'\n\1', text, flags=re.IGNORECASE)

    # Rapikan spasi di sekitar tanda baca
    text = re.sub(r'\s([,.])', r'\1', text)

    # Hapus newline ganda
    text = re.sub(r'\n+', '\n', text)

    # Capitalize baris awal jika perlu
    lines = [line.strip().capitalize() for line in text.split("\n") if line.strip()]
    formatted_text = "\n".join(lines)

    return formatted_text


# ==========================================================
# 🔁 AUTO RETRAIN (simulasi, berjalan di thread terpisah)
# ==========================================================
def auto_retrain_if_needed():
    """Melatih ulang model EasyOCR secara otomatis ketika dataset bertambah (simulasi)"""
    def retrain():
        dataset = load_dataset()
        total_data = sum(len(v) for v in dataset.values())
        trained_flag = os.path.join('model', 'last_trained.txt')
        os.makedirs('model', exist_ok=True)

        last_trained = 0
        if os.path.exists(trained_flag):
            with open(trained_flag, 'r') as f:
                last_trained = int(f.read().strip() or 0)

        if total_data > last_trained:
            print(f"🧠 [Auto-Retrain] Dataset bertambah ({last_trained} → {total_data}). Melatih ulang model (simulasi)...")
            import time
            time.sleep(2)
            with open(trained_flag, 'w') as f:
                f.write(str(total_data))
            print("✅ [Auto-Retrain] Model EasyOCR diperbarui berdasarkan dataset terbaru!")
        else:
            print("✅ Model sudah sesuai dengan dataset terbaru.")

    threading.Thread(target=retrain, daemon=True).start()
