import json
import os
import time
from config import Config

def allowed_file(filename):
    """Cek apakah file diizinkan berdasarkan ekstensi"""
    return "." in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def load_dataset():
    """Memuat dataset dari file JSON"""
    if os.path.exists(Config.DATASET_JSON):
        with open(Config.DATASET_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"surat_izin": [], "surat_sakit": []}


def save_dataset(dataset):
    """Menyimpan dataset ke file JSON"""
    with open(Config.DATASET_JSON, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)


def hapus_file_lama():
    """Menghapus file upload yang sudah kadaluarsa"""
    skrg = time.time()
    for filename in os.listdir(Config.UPLOAD_FOLDER):
        if filename.endswith(".time"):
            folder = os.path.join(Config.UPLOAD_FOLDER, filename)
            with open(folder, "r") as f:
                wtu_upload = float(f.read().strip())
            if skrg - wtu_upload > Config.TIMEOUT:
                basefile = folder.replace(".time", "")
                if os.path.exists(basefile):
                    os.remove(basefile)
                os.remove(folder)


def auto_label(text):
    """
    Memberi label otomatis berdasarkan isi teks hasil OCR.
    - Jika mengandung kata 'izin' → surat_izin
    - Jika mengandung kata 'sakit' → surat_sakit
    - Jika tidak keduanya → surat_lain
    """
    text_lower = text.lower()
    if "izin" in text_lower:
        return "surat_izin"
    elif "sakit" in text_lower:
        return "surat_sakit"
    else:
        return "surat_lain"
