from flask import Flask
from config import Config
from utils import hapus_file_lama
from routes.main_routes import main_bp
from routes.dataset_routes import dataset_bp

# 1. Inisialisasi aplikasi
app = Flask(__name__)

# 2. Inisialisasi folder
Config.init_folders()

# 3. Register blueprints
app.register_blueprint(main_bp)
app.register_blueprint(dataset_bp)

# Middleware untuk hapus file lama
@app.before_request
def cleanup():
    hapus_file_lama()

# 4. Aplikasi dimulai
if __name__ == "__main__":
    app.run(host=Config.HOST, debug=Config.DEBUG)