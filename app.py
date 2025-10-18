from flask import Flask, render_template, request, jsonify
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import os
import time
import uuid
import traceback

app = Flask(__name__)

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"} # ekstensi yang diizinkan
TIMEOUT = 60 # detik

def allowed_file(filename):
    return "." in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

# Rute/proses aplikasi
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    try:
        if "file" not in request.files:
            return "Tidak ada file yang diupload", 400
        
        f = request.files["file"]
        if f.filename == "":
            return "Nama file kosong", 400
        
        # random nama file untuk menghindari kesamaan nama
        nama_unik = f"{uuid.uuid4().hex}_{f.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, nama_unik)
        f.save(file_path)

        # Simpan waktu upload
        with open(file_path + ".time", "w") as t:
            t.write(str(time.time()))

        # Proses Optical Character Recognition (OCR)
        if f.filename.lower().endswith(".pdf"):
            print(f"📄 Mendeteksi file PDF: {file_path}")
            pages = convert_from_path(file_path)  # Tanpa poppler_path, karena sudah ada di PATH
            print(f"✅ PDF berhasil dikonversi ke {len(pages)} halaman")
            text = "\n\n".join([pytesseract.image_to_string(pages) for page in pages])
        else:
            print(f"🖼️ Mendeteksi file gambar: {file_path}")
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)

        return render_template("result.html", text=text)
    
    except Exception as e:
        print("❌ ERROR TERJADI:")
        traceback.print_exc()
        return f"<pre>{traceback.format_exc()}</pre>", 500
    
@app.before_request
def hapus_file_lama():
    skrg = time.time()
    for filename in os.listdir(UPLOAD_FOLDER):
        if filename.endswith(".time"):
            folder = os.path.join(UPLOAD_FOLDER, filename)
            with open(folder, "r") as f:
                wtu_upload = float(f.read().strip())
            if skrg - wtu_upload > TIMEOUT:
                # Hapus file dan metadatanya
                basefile = folder.replace(".time", "")
                if os.path.exists(basefile):
                    os.remove(basefile)
                os.remove(folder)

# Menggunakan jsonify untuk mengembalikan respons JSON
@app.route("/bersihkan", methods =["POST"])
def bersihkan_file_user():
    hapus_file_lama()
    return jsonify({"status" : "ok bersih"}), 200



if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)

