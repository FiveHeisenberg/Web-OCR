# 🖼️ Digital Image Processing Project

## 📌 Overview
This project was developed as part of the **Digital Image** course.  
It focuses on applying fundamental and advanced concepts in **digital image processing** to build a functional and structured application.

## 👨‍💻 Contributors
- Rifki Maulana  
- Reyza Maulana  
- Arya Dwi Pangga Handoko  
- Bintang Ramadhan

## 🧠 Purpose
- To demonstrate practical implementation of digital image processing techniques.  
- To strengthen understanding of theoretical concepts through real-world applications.  
- To fulfill the course project requirements.

## 🛠️ Tech Stack
- **Programming Language:** Python  
- **Libraries:** OpenCV, NumPy, Matplotlib *(or adjust according to the actual stack you used)*  
- **Tools:** Jupyter Notebook / VS Code *(optional, adjust if needed)*

## How To Run
Check python Version or install before use this project
## 1. use cmd and change directory to project folder : cd "D:\Kuliah\P.citra\OCR PRoject\Web-OCR"
## 2. create venv : python -m venv venv
## 3. after create activate venv : venv\Scripts\activate
## 4. Upgrade pip before start this project : python -m pip install --upgrade pip
## 5. Install all dependencies from requirements.txt : python -m pip install -r requirements.txt
## 6. run the application with flask : 
## set FLASK_APP=app.py
## set FLASK_ENV=development
## flask run
## 7. run with app.py : python app.py
## 8. instal Tesseract if you call url_for('static') : https://github.com/UB-Mannheim/tesseract/wiki

## Solved problem alert with library
## ctrl + shift + p, search python select interpreter and select folder venv\Scripts\python.exe

 

## 📂 Project Structure
```
Web-OCR/
├── 📁 dataset/             # Folder dataset
│   ├── 📁 surat_izin/
│   ├── 📁 surat_sakit/
│   └──  dataset.json
├── 📁 routes/              # Blueprint untuk routing
│   ├── __init__.py
│   ├── dataset_routes.py   # Route untuk manajemen dataset
│   └── main_routes.py      # Route untuk halaman utama dan upload
├── 📁 static/
│   ├── 📁 css/
│   ├── 📁 images/
│   └── 📁 js/
├── 📁 templates/           # Template HTML
│   ├── dataset.html
│   ├── index.html
│   └── result.html
├── 📁 uploads/             # Folder upload temporary
├── 📄 app.py               # File utama aplikasi Flask
├── 📄 classifier.py        # Klasifikasi jenis surat (PDF atau IMG)
├── 📄 config.py            # Konfigurasi aplikasi
├── 📄 extractor.py         # Ekstraksi informasi dari teks
├── 📄 ocr_processor.py     # Pemrosesan OCR
├── 📄 requirements.txt     # Dependencies
└── 📄 utils.py             # Fungsi utilitas umum
```
---

## ⚠️⚠️Konfigurasi - Ganti Path Popler dan Tesserect

### config.py
```bash
import os

class Config:
    # Ganti Path nya sesuai tempat path tesseract 
    TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    
    # Ganti Path nya sesuai tempat path Popler
    POPPLER_PATH = r"C:\MY FILES\APPS\Poppler\poppler-25.07.0\Library\bin"
```
---


## 🔄 Alur Pemakaian
```
┌──────────────────────────────────────────────────────────┐
│ USER: Buka browser → http://localhost:5000/              │
└───────────────────┬──────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────┐
│ app.py: Flask menerima request                           │
└───────────────────┬──────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────┐
│ routes/main_routes.py: Route "/" dipanggil               │
│  - Load dataset dari utils.py                            │
│  - Hitung statistik                                      │
│  - Render template HTML                                  │
└───────────────────┬──────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────┐
│ BROWSER: Tampilkan halaman dengan form upload            │
└───────────────────┬──────────────────────────────────────┘
                    ↓
           USER: Upload file
                    ↓
┌──────────────────────────────────────────────────────────┐
│ routes/main_routes.py: Route "/upload" (POST)            │
│  1. Terima file                                          │
│  2. Simpan ke /uploads                                   │
└───────────────────┬──────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────┐
│ ocr_processor.py: Proses OCR                             │
│  - Baca file (PDF/Gambar)                                │
│  - Tesseract extract teks                                │
│  - Return: text mentah                                   │
└───────────────────┬──────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────┐
│ classifier.py: Klasifikasi                               │
│  - Cari kata kunci "izin" vs "sakit"                     │
│  - Hitung score                                          │
│  - Return: "surat_izin" atau "surat_sakit"               │
└───────────────────┬──────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────┐
│ extractor.py: Ekstrak info                               │
│  - Regex pattern untuk nama                              │
│  - Regex pattern untuk NIM                               │
│  - Regex pattern untuk tanggal                           │
│  - Return: dictionary info lengkap                       │
└───────────────────┬──────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────┐
│ routes/main_routes.py: Render result.html                │
│  - Kirim: text, jenis_surat, info                        │
└───────────────────┬──────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────┐
│ BROWSER: Tampilkan hasil ekstraksi                       │
└──────────────────────────────────────────────────────────┘

