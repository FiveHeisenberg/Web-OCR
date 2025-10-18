from flask import Flask, render_template, request
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import os
import traceback

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

        file_path = os.path.join(UPLOAD_FOLDER, f.filename)
        f.save(file_path)

        if f.filename.lower().endswith(".pdf"):
            print(f"📄 Mendeteksi file PDF: {file_path}")
            pages = convert_from_path(file_path)  # Tanpa poppler_path, karena sudah ada di PATH
            print(f"✅ PDF berhasil dikonversi ke {len(pages)} halaman")
            text = "\n\n".join([pytesseract.image_to_string(page) for page in pages])
        else:
            print(f"🖼️ Mendeteksi file gambar: {file_path}")
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)

        return render_template("result.html", text=text)
    
    except Exception as e:
        print("❌ ERROR TERJADI:")
        traceback.print_exc()
        return f"<pre>{traceback.format_exc()}</pre>", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)

