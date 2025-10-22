from flask import Blueprint, render_template, request, jsonify
import os
import time
import uuid
import traceback
from config import Config
from utils import load_dataset, hapus_file_lama
from ocr_processor import process_file
from classifier import classify_letter
from extractor import extract_info

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    # 1. Halaman utama
    dataset = load_dataset()
    
    # 2. Hitung jumlah data
    stats = {
        "total": len(dataset["surat_izin"]) + len(dataset["surat_sakit"]),
        "izin": len(dataset["surat_izin"]),
        "sakit": len(dataset["surat_sakit"])
    }
    
    # 3. Tampilkan halaman HTML
    return render_template("index.html", stats=stats)

# Fungsi Menerima Upload
@main_bp.route("/upload", methods=["POST"])
def upload():
    try:
        if "file" not in request.files:
            return "Tidak ada file yang diupload", 400
        
        # 1. Mengambil file dari Form
        f = request.files["file"]
        if f.filename == "":
            return "Nama file kosong", 400
        
        # 2. Simpan file
        nama_unik = f"{uuid.uuid4().hex}_{f.filename}"
        
        # 3. Simpan file ke folder uploads
        file_path = os.path.join(Config.UPLOAD_FOLDER, nama_unik)
        f.save(file_path)

        # Simpan timestamp
        with open(file_path + ".time", "w") as t:
            t.write(str(time.time()))

        # 4. Proses OCR
        text = process_file(file_path, f.filename)
        
        # 5. Klasifikasi jenis surat
        jenis_surat = classify_letter(text)
        
        # 6. Ekstrak informasi
        info = extract_info(text, jenis_surat)
        
        # 7. Menampilkan hasil
        return render_template("result.html", text=text, jenis=jenis_surat, info=info)
    
    except Exception as e:
        print("❌ ERROR TERJADI:")
        traceback.print_exc()
        return f"<pre>{traceback.format_exc()}</pre>", 500

@main_bp.route("/bersihkan", methods=["POST"])
def bersihkan_file_user():
    """Bersihkan file lama"""
    hapus_file_lama()
    return jsonify({"status": "ok bersih"}), 200