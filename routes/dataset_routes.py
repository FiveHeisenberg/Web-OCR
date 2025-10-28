from flask import Blueprint, render_template, request, jsonify
import os
import uuid
import traceback
from datetime import datetime
from config import Config
from utils import load_dataset, save_dataset
from ocr_processor import process_file, auto_retrain_if_needed
from extractor import extract_info

dataset_bp = Blueprint('dataset', __name__, url_prefix='/dataset')


def auto_label(text):
    """Deteksi otomatis jenis surat dari teks OCR"""
    text_lower = text.lower()
    if "sakit" in text_lower:
        return "surat_sakit"
    elif "izin" in text_lower:
        return "surat_izin"
    else:
        return "tidak_terdeteksi"


@dataset_bp.route("/")
def dataset_page():
    """Halaman manajemen dataset"""
    dataset = load_dataset()
    return render_template("dataset.html", dataset=dataset)


@dataset_bp.route("/add", methods=["POST"])
def add_to_dataset():
    """Menambahkan data ke dataset (auto-label aktif + auto retrain EasyOCR)"""
    try:
        if "file" not in request.files:
            return jsonify({"error": "Tidak ada file"}), 400

        f = request.files["file"]

        # Simpan file sementara
        filename = f"{uuid.uuid4().hex}_{f.filename}"
        temp_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        f.save(temp_path)

        # Jalankan OCR (sekarang menggunakan EasyOCR dari ocr_processor.py)
        text = process_file(temp_path, f.filename)

        # Tentukan label otomatis
        jenis = auto_label(text)

        # Jika tidak terdeteksi, hapus file dan batalkan simpan
        if jenis == "tidak_terdeteksi":
            os.remove(temp_path)
            return jsonify({
                "error": "Jenis surat tidak dapat dideteksi secara otomatis. Pastikan teks mengandung kata 'izin' atau 'sakit'."
            }), 400

        # Pindahkan file ke folder dataset sesuai label
        dataset_path = os.path.join(Config.DATASET_FOLDER, jenis, filename)
        os.rename(temp_path, dataset_path)

        # Ekstrak informasi tambahan
        info = extract_info(text, jenis)

        # Tambahkan ke dataset.json
        dataset = load_dataset()
        entry = {
            "id": str(uuid.uuid4()),
            "filename": filename,
            "path": dataset_path,
            "jenis": jenis,
            "text": text,
            "info": info,
            "created_at": datetime.now().isoformat()
        }
        dataset[jenis].append(entry)
        save_dataset(dataset)

        # 🔁 Panggil auto retrain (akan berjalan otomatis di background)
        auto_retrain_if_needed()

        return jsonify({"success": True, "data": entry}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@dataset_bp.route("/list", methods=["GET"])
def list_dataset():
    """Menampilkan daftar dataset"""
    dataset = load_dataset()
    return jsonify(dataset), 200


@dataset_bp.route("/delete/<jenis>/<entry_id>", methods=["DELETE"])
def delete_from_dataset(jenis, entry_id):
    """Menghapus entry dari dataset"""
    try:
        dataset = load_dataset()

        if jenis not in dataset:
            return jsonify({"error": "Jenis tidak valid"}), 400

        # Cari dan hapus entry
        entry_to_delete = None
        for i, entry in enumerate(dataset[jenis]):
            if entry["id"] == entry_id:
                entry_to_delete = entry
                dataset[jenis].pop(i)
                break

        if entry_to_delete:
            # Hapus file fisik
            if os.path.exists(entry_to_delete["path"]):
                os.remove(entry_to_delete["path"])

            save_dataset(dataset)
            return jsonify({"success": True}), 200

        return jsonify({"error": "Entry tidak ditemukan"}), 404

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
