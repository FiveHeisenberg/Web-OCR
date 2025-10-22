from flask import Blueprint, render_template, request, jsonify
import os
import uuid
import traceback
from datetime import datetime
from config import Config
from utils import load_dataset, save_dataset
from ocr_processor import process_file
from extractor import extract_info

dataset_bp = Blueprint('dataset', __name__, url_prefix='/dataset')

@dataset_bp.route("/")
def dataset_page():
    """Halaman manajemen dataset"""
    dataset = load_dataset()
    return render_template("dataset.html", dataset=dataset)

@dataset_bp.route("/add", methods=["POST"])
def add_to_dataset():
    """Menambahkan data ke dataset"""
    try:
        if "file" not in request.files:
            return jsonify({"error": "Tidak ada file"}), 400
        
        f = request.files["file"]
        jenis = request.form.get("jenis", "surat_izin")
        
        if jenis not in ["surat_izin", "surat_sakit"]:
            return jsonify({"error": "Jenis surat tidak valid"}), 400
        
        # Simpan file ke folder dataset
        filename = f"{uuid.uuid4().hex}_{f.filename}"
        dataset_path = os.path.join(Config.DATASET_FOLDER, jenis, filename)
        f.save(dataset_path)
        
        # Proses OCR
        text = process_file(dataset_path, f.filename)
        
        # Ekstrak informasi
        info = extract_info(text, jenis)
        
        # Simpan ke dataset
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

@dataset_bp.route("/train", methods=["POST"])
def train_model():
    """Simulasi training model dengan dataset"""
    try:
        dataset = load_dataset()
        
        total_data = len(dataset["surat_izin"]) + len(dataset["surat_sakit"])
        
        if total_data == 0:
            return jsonify({"error": "Dataset masih kosong"}), 400
        
        # Simulasi training (dalam implementasi nyata, ini akan melatih model ML)
        stats = {
            "total_data": total_data,
            "surat_izin": len(dataset["surat_izin"]),
            "surat_sakit": len(dataset["surat_sakit"]),
            "status": "Training berhasil (simulasi)",
            "accuracy": "Estimasi 85-90% (berdasarkan dataset)"
        }
        
        return jsonify(stats), 200
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500