from flask import Blueprint, render_template, request, jsonify
import os
import time
import uuid
import traceback
from datetime import datetime

from config import Config
from utils import load_dataset, save_dataset, hapus_file_lama
from ocr_processor import process_file
from classifier import classify_letter
from extractor import extract_info

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    """Halaman utama"""
    dataset = load_dataset()
    stats = {
        "total": len(dataset["surat_izin"]) + len(dataset["surat_sakit"]),
        "izin": len(dataset["surat_izin"]),
        "sakit": len(dataset["surat_sakit"])
    }
    return render_template("index.html", stats=stats)


@main_bp.route("/upload", methods=["POST"])
def upload():
    """Upload file dan otomatis masuk dataset"""
    try:
        if "file" not in request.files:
            return "Tidak ada file yang diupload", 400
        
        f = request.files["file"]
        if f.filename == "":
            return "Nama file kosong", 400

        # 1. Simpan file sementara
        nama_unik = f"{uuid.uuid4().hex}_{f.filename}"
        file_path = os.path.join(Config.UPLOAD_FOLDER, nama_unik)
        f.save(file_path)

        # 2. Simpan timestamp untuk auto-cleanup
        with open(file_path + ".time", "w") as t:
            t.write(str(time.time()))

        # 3. Jalankan OCR
        text = process_file(file_path, f.filename)

        # 4. Auto klasifikasi jenis surat (izin/sakit)
        jenis_surat = classify_letter(text)

        # 5. Ekstraksi informasi penting
        info = extract_info(text, jenis_surat)

        # 🟢 6. AUTO-LABEL: simpan otomatis ke dataset
        dataset = load_dataset()
        filename_dataset = f"{uuid.uuid4().hex}_{f.filename}"
        dataset_path = os.path.join(Config.DATASET_FOLDER, jenis_surat, filename_dataset)

        # Pindahkan file dari uploads ke dataset folder
        os.rename(file_path, dataset_path)

        # Simpan entry baru ke dataset JSON
        entry = {
            "id": str(uuid.uuid4()),
            "filename": filename_dataset,
            "path": dataset_path,
            "jenis": jenis_surat,
            "text": text,
            "info": info,
            "created_at": datetime.now().isoformat()
        }
        dataset[jenis_surat].append(entry)
        save_dataset(dataset)

        # Tampilkan hasil + notifikasi auto-label sukses
        return render_template(
            "result.html",
            text=text,
            jenis=jenis_surat,
            info=info,
            auto_label=True  # agar di HTML bisa ditampilkan "Data otomatis tersimpan ke dataset"
        )

    except Exception as e:
        print("❌ ERROR TERJADI:")
        traceback.print_exc()
        return f"<pre>{traceback.format_exc()}</pre>", 500


@main_bp.route("/bersihkan", methods=["POST"])
def bersihkan_file_user():
    """Bersihkan file lama"""
    hapus_file_lama()
    return jsonify({"status": "ok bersih"}), 200
