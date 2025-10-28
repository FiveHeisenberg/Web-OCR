import os

class Config:
    """Konfigurasi aplikasi"""
    
    # Tesseract OCR
    TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    # Poppler PDF
    POPPLER_PATH = r"E:\poppler\Library\bin"

    # Folder utama
    UPLOAD_FOLDER = "uploads"
    DATASET_FOLDER = "dataset"
    DATASET_JSON = "dataset/dataset.json"

    # 🔥 Tambahkan ini:
    MODEL_FOLDER = "model"  # Folder untuk menyimpan model ML hasil training
    MODEL_FILE = "classifier_model.pkl"

    # File settings
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}
    TIMEOUT = 60  # detik

    # Flask
    DEBUG = True
    HOST = "0.0.0.0"

    @staticmethod
    def init_folders():
        """Membuat folder-folder yang diperlukan"""
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.DATASET_FOLDER, exist_ok=True)
        os.makedirs(os.path.join(Config.DATASET_FOLDER, "surat_izin"), exist_ok=True)
        os.makedirs(os.path.join(Config.DATASET_FOLDER, "surat_sakit"), exist_ok=True)
        os.makedirs(Config.MODEL_FOLDER, exist_ok=True)  # 🔥 pastikan folder model juga dibuat
