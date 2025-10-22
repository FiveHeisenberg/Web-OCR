from pdf2image import convert_from_path
from PIL import Image
import pytesseract
from config import Config

# Set path tesseract
pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_CMD

def process_file(file_path, filename):
    # Cek: PDF atau Gambar?
    if filename.lower().endswith(".pdf"):
        return process_pdf(file_path)
    else:
        return process_image(file_path)

def process_pdf(file_path):
    # 1. Konversi PDF jadi gambar (pakai poppler)
    pages = convert_from_path(file_path, poppler_path=Config.POPPLER_PATH)
    
    # 2. OCR setiap halaman (pakai tesseract)
    texts = []
    for page in pages:
        text = pytesseract.image_to_string(page, lang='ind+eng')
        texts.append(text)
    print(texts)
    
    # 3. Gabungkan semua teks
    return "\n\n".join(texts)

def process_image(file_path):
    # 1. Buka gambar
    print(f"🖼️ Mendeteksi file gambar: {file_path}")
    image = Image.open(file_path)
    
    # 2. OCR langsung
    text = pytesseract.image_to_string(image, lang='ind+eng')
    return text