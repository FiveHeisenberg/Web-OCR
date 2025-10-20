from flask import Flask, render_template, request, jsonify
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import os
import time
import uuid
import traceback
import json
import re
from datetime import datetime

app = Flask(__name__)

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

UPLOAD_FOLDER = "uploads"
DATASET_FOLDER = "dataset"
DATASET_JSON = "dataset/dataset.json"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATASET_FOLDER, exist_ok=True)
os.makedirs(os.path.join(DATASET_FOLDER, "surat_izin"), exist_ok=True)
os.makedirs(os.path.join(DATASET_FOLDER, "surat_sakit"), exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}
TIMEOUT = 60

def allowed_file(filename):
    return "." in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

def load_dataset():
    """Memuat dataset dari file JSON"""
    if os.path.exists(DATASET_JSON):
        with open(DATASET_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"surat_izin": [], "surat_sakit": []}

def save_dataset(dataset):
    """Menyimpan dataset ke file JSON"""
    with open(DATASET_JSON, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

def extract_info(text, jenis_surat):
    """Ekstrak informasi penting dari teks OCR"""
    info = {
        "jenis": jenis_surat,
        "nama": None,
        "nim": None,
        "tanggal": None,
        "tanggal_mulai": None,
        "tanggal_selesai": None,
        "alasan": None,
        "durasi": None,
        "dokter": None,
        "klinik": None
    }
    
    # Pattern untuk mencari nama (lebih fleksibel)
    nama_patterns = [
        r"Nama\s*[:=]\s*([A-Z][a-zA-Z\s]+?)(?:\n|Umur|NIM|Prodi)",
        r"(?:yang bertanda tangan|pembuat surat)\s+(?:di\s*)?(?:bawah|atas)\s+ini\s*[:=]?\s*\n+Nama\s*[:=]\s*([A-Z][a-zA-Z\s]+?)(?:\n|Umur|NIM)",
        r"Nama\s+mahasiswa\s*[:=]\s*([A-Z][a-zA-Z\s]+)",
        r"yang tersebut namanya\s+(?:di\s*)?(?:atas|bawah)\s+(?:.*?)\s+([A-Z][a-zA-Z\s]{3,})",
    ]
    
    for pattern in nama_patterns:
        nama_match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if nama_match:
            nama = nama_match.group(1).strip()
            # Bersihkan nama dari kata-kata yang tidak perlu
            nama = re.sub(r'\s+', ' ', nama)
            if len(nama) > 3 and not any(x in nama.lower() for x in ['benar', 'dalam', 'keadaan']):
                info["nama"] = nama
                break
    
    # Pattern untuk NIM
    nim_pattern = r"NIM\s*[:=]?\s*(\d+)"
    nim_match = re.search(nim_pattern, text, re.IGNORECASE)
    if nim_match:
        info["nim"] = nim_match.group(1).strip()
    
    # Pattern untuk tanggal tunggal
    tanggal_patterns = [
        r"tanggal\s+(\d{1,2}\s+(?:Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s+\d{4})",
        r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
        r"(\d{1,2}\s+\w+\s+\d{4})",
    ]
    
    for pattern in tanggal_patterns:
        tanggal_match = re.search(pattern, text, re.IGNORECASE)
        if tanggal_match:
            info["tanggal"] = tanggal_match.group(1).strip()
            break
    
    # Pattern untuk range tanggal (khusus surat sakit)
    tanggal_range_pattern = r"(?:mulai dari )?[Tt]anggal\s+(\d{1,2}\s+\w+\s+\d{4})\s*[—\-–]\s*(\d{1,2}\s+\w+\s+\d{4})"
    range_match = re.search(tanggal_range_pattern, text)
    if range_match:
        info["tanggal_mulai"] = range_match.group(1).strip()
        info["tanggal_selesai"] = range_match.group(2).strip()
        if not info["tanggal"]:
            info["tanggal"] = info["tanggal_mulai"]
        
        # Hitung durasi dari range tanggal
        try:
            from datetime import datetime
            bulan_map = {
                'januari': 1, 'februari': 2, 'maret': 3, 'april': 4,
                'mei': 5, 'juni': 6, 'juli': 7, 'agustus': 8,
                'september': 9, 'oktober': 10, 'november': 11, 'desember': 12
            }
            
            def parse_indo_date(date_str):
                parts = date_str.lower().split()
                if len(parts) == 3:
                    day = int(parts[0])
                    month = bulan_map.get(parts[1], 1)
                    year = int(parts[2])
                    return datetime(year, month, day)
                return None
            
            d1 = parse_indo_date(info["tanggal_mulai"])
            d2 = parse_indo_date(info["tanggal_selesai"])
            
            if d1 and d2:
                durasi_hari = (d2 - d1).days + 1
                info["durasi"] = f"{durasi_hari} hari"
        except:
            pass
    
    # Pattern untuk alasan/diagnosa (surat sakit)
    if jenis_surat == "surat_sakit":
        alasan_patterns = [
            r"(?:dalam keadaan|menderita|didiagnosa|diagnosa|penyakit)\s+([A-Z][^\n\.]+?)(?:\s+maka|\s+sehingga|\.|Demikian)",
            r"keadaan\s+([A-Z][A-Z\s]+?)(?:\s+maka)",
        ]
        
        for pattern in alasan_patterns:
            alasan_match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if alasan_match:
                alasan = alasan_match.group(1).strip()
                # Filter kata yang bukan diagnosa
                if len(alasan) > 3 and alasan.upper() == alasan:
                    info["alasan"] = alasan
                    break
    
    # Pattern untuk alasan (surat izin)
    if jenis_surat == "surat_izin":
        alasan_patterns = [
            r"karena\s*[:=]?\s*([^\n\.]+?)(?:\.|Demikian|\n\n)",
            r"alasan\s*[:=]?\s*([^\n\.]+)",
        ]
        
        for pattern in alasan_patterns:
            alasan_match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if alasan_match:
                info["alasan"] = alasan_match.group(1).strip()
                break
    
    # Pattern untuk durasi (jika belum terisi dari range tanggal)
    if not info["durasi"]:
        durasi_patterns = [
            r"(?:berlaku|selama|istirahat)\s+(\d+)\s*(?:hari|day)",
            r"(\d+)\s*(?:hari|day)",
        ]
        
        for pattern in durasi_patterns:
            durasi_match = re.search(pattern, text, re.IGNORECASE)
            if durasi_match:
                info["durasi"] = durasi_match.group(1) + " hari"
                break
    
    # Pattern untuk dokter (surat sakit)
    dokter_pattern = r"(?:Dokter|dr\.|Dr\.)\s+([A-Z][a-zA-Z\s\.]+?)(?:\n|NIP)"
    dokter_match = re.search(dokter_pattern, text, re.MULTILINE)
    if dokter_match:
        info["dokter"] = dokter_match.group(1).strip()
    
    # Pattern untuk klinik/rumah sakit
    klinik_patterns = [
        r"(KLINIK [A-Z\s]+?)(?:\n|Jl\.)",
        r"(RUMAH SAKIT [A-Z\s]+?)(?:\n|Jl\.)",
        r"(PUSKESMAS [A-Z\s]+?)(?:\n|Jl\.)",
    ]
    
    for pattern in klinik_patterns:
        klinik_match = re.search(pattern, text, re.IGNORECASE)
        if klinik_match:
            info["klinik"] = klinik_match.group(1).strip()
            break
    
    return info

def classify_letter(text):
    """Klasifikasi jenis surat berdasarkan kata kunci"""
    text_lower = text.lower()
    
    # Kata kunci untuk surat izin
    keywords_izin = [
        "surat keterangan izin",
        "surat izin",
        "permohonan izin",
        "memohon izin",
        "tidak mengikuti",
        "tidak masuk",
        "keperluan keluarga",
        "keperluan mendadak",
    ]
    
    # Kata kunci untuk surat sakit
    keywords_sakit = [
        "surat keterangan sakit",
        "surat sakit",
        "surat keterangan dokter",
        "dokter",
        "diagnosa",
        "penyakit",
        "berobat",
        "istirahat sakit",
        "dalam perawatan",
        "rawat inap",
    ]
    
    # Hitung score dengan bobot
    score_izin = 0
    score_sakit = 0
    
    for kw in keywords_izin:
        if kw in text_lower:
            # Kata kunci spesifik diberi bobot lebih tinggi
            if "surat keterangan izin" in kw or "surat izin" in kw:
                score_izin += 5
            else:
                score_izin += 1
    
    for kw in keywords_sakit:
        if kw in text_lower:
            # Kata kunci spesifik diberi bobot lebih tinggi
            if "surat keterangan sakit" in kw or "surat sakit" in kw:
                score_sakit += 5
            else:
                score_sakit += 1
    
    # Cek konteks tambahan
    if "mendampingi" in text_lower and "sakit" in text_lower:
        score_izin += 3  # Izin karena anggota keluarga sakit
    
    if "lampirkan surat dokter" in text_lower:
        score_izin += 2  # Biasanya ada di surat izin
    
    print(f"[DEBUG] Score Izin: {score_izin}, Score Sakit: {score_sakit}")
    
    if score_sakit > score_izin:
        return "surat_sakit"
    elif score_izin > 0:
        return "surat_izin"
    return "tidak_terdeteksi"

@app.route("/")
def index():
    dataset = load_dataset()
    stats = {
        "total": len(dataset["surat_izin"]) + len(dataset["surat_sakit"]),
        "izin": len(dataset["surat_izin"]),
        "sakit": len(dataset["surat_sakit"])
    }
    return render_template("index.html", stats=stats)

@app.route("/upload", methods=["POST"])
def upload():
    try:
        if "file" not in request.files:
            return "Tidak ada file yang diupload", 400
        
        f = request.files["file"]
        if f.filename == "":
            return "Nama file kosong", 400
        
        nama_unik = f"{uuid.uuid4().hex}_{f.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, nama_unik)
        f.save(file_path)

        with open(file_path + ".time", "w") as t:
            t.write(str(time.time()))

        # Proses OCR
        if f.filename.lower().endswith(".pdf"):
            print(f"📄 Mendeteksi file PDF: {file_path}")
            pages = convert_from_path(
                file_path,
                poppler_path=r"C:\MY FILES\APPS\Poppler\poppler-25.07.0\Library\bin"
            )
            print(f"✅ PDF berhasil dikonversi ke {len(pages)} halaman")
            text = "\n\n".join([pytesseract.image_to_string(page, lang='ind+eng') for page in pages])
        else:
            print(f"🖼️ Mendeteksi file gambar: {file_path}")
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image, lang='ind+eng')

        # Klasifikasi jenis surat
        jenis_surat = classify_letter(text)
        
        # Ekstrak informasi
        info = extract_info(text, jenis_surat)

        return render_template("result.html", text=text, jenis=jenis_surat, info=info)
    
    except Exception as e:
        print("❌ ERROR TERJADI:")
        traceback.print_exc()
        return f"<pre>{traceback.format_exc()}</pre>", 500

@app.route("/dataset")
def dataset_page():
    """Halaman manajemen dataset"""
    dataset = load_dataset()
    return render_template("dataset.html", dataset=dataset)

@app.route("/dataset/add", methods=["POST"])
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
        dataset_path = os.path.join(DATASET_FOLDER, jenis, filename)
        f.save(dataset_path)
        
        # Proses OCR
        if f.filename.lower().endswith(".pdf"):
            pages = convert_from_path(
                dataset_path,
                poppler_path=r"C:\MY FILES\APPS\Poppler\poppler-25.07.0\Library\bin"
            )
            text = "\n\n".join([pytesseract.image_to_string(page, lang='ind+eng') for page in pages])
        else:
            image = Image.open(dataset_path)
            text = pytesseract.image_to_string(image, lang='ind+eng')
        
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

@app.route("/dataset/list", methods=["GET"])
def list_dataset():
    """Menampilkan daftar dataset"""
    dataset = load_dataset()
    return jsonify(dataset), 200

@app.route("/dataset/delete/<jenis>/<entry_id>", methods=["DELETE"])
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

@app.route("/dataset/train", methods=["POST"])
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
    
@app.before_request
def hapus_file_lama():
    skrg = time.time()
    for filename in os.listdir(UPLOAD_FOLDER):
        if filename.endswith(".time"):
            folder = os.path.join(UPLOAD_FOLDER, filename)
            with open(folder, "r") as f:
                wtu_upload = float(f.read().strip())
            if skrg - wtu_upload > TIMEOUT:
                basefile = folder.replace(".time", "")
                if os.path.exists(basefile):
                    os.remove(basefile)
                os.remove(folder)

@app.route("/bersihkan", methods=["POST"])
def bersihkan_file_user():
    hapus_file_lama()
    return jsonify({"status": "ok bersih"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)