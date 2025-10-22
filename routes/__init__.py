"""
Package untuk semua routes aplikasi
"""

from .main_routes import main_bp
from .dataset_routes import dataset_bp

__all__ = ['main_bp', 'dataset_bp']