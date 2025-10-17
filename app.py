from flask import Flask, render_template, request, redirect, url_for, send_file
from PIL import Image
from pdf2image import convert_from_bytes
import pytesseract
import base64
import io

app = Flask(__name__)


# ==========================
# Fungsi bantu OCR
# ==========================
def preprocess_image_pil(pil_image):
    """Lakukan preprocessing sederhana pada citra sebelum OCR (jika perlu)."""
    # Tambahkan logika preprocessing di sini jika ingin
    return pil_image


def ocr_image_from_pil(pil_image, lang='eng'):
    """Melakukan OCR dari objek PIL Image."""
    # Jika preprocess hanya mengembalikan PIL image, langsung pakai
    th = preprocess_image_pil(pil_image)
    
    # Jangan pakai Image.fromarray di sini karena sudah berupa PIL image
    text = pytesseract.image_to_string(th, lang=lang)
    return text


# ==========================
# Route utama
# ==========================
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(url_for('index'))

    f = request.files['file']
    if f.filename == '':
        return redirect(url_for('index'))

    filename = f.filename.lower()
    text_results = []

    # Jika file berupa PDF → konversi tiap halaman ke gambar
    if filename.endswith('.pdf'):
        pdf_bytes = f.read()
        pil_pages = convert_from_bytes(pdf_bytes)

        for i, pil in enumerate(pil_pages):
            text = ocr_image_from_pil(pil)
            text_results.append((f'page_{i+1}', text))

    else:
        # Asumsi file berupa gambar
        pil = Image.open(f.stream).convert('RGB')
        text = ocr_image_from_pil(pil)
        text_results.append(('image', text))

    # Gabungkan semua teks hasil OCR
    full_text = "\n\n".join([t for _, t in text_results])

    return render_template('result.html', text=full_text)


@app.route('/capture', methods=['POST'])
def capture():
    # Menerima data gambar base64 dari frontend
    data_url = request.form.get('image_data')
    if not data_url:
        return ('', 400)

    header, encoded = data_url.split(',', 1)
    image_bytes = io.BytesIO(base64.b64decode(encoded))

    pil = Image.open(image_bytes).convert('RGB')
    text = ocr_image_from_pil(pil)

    return render_template('result.html', text=text)


# ==========================
# Main program
# ==========================
if __name__ == '__main__':
    app.run(debug=True)
