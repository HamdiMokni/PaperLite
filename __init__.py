__version__ = "2.0.0"
__author__ = "PDF Compressor Team"
__description__ = "Enhanced PDF B&W Compressor with Advanced Features"

from .performance_tracker import PerformanceTracker
from .file_utils import get_file_size, calculate_timeout, safe_remove_file, create_temp_file
from .pdf_compressor import compress_single_pdf, check_ghostscript
from .batch_processor import compress_directory, compress_single_file_wrapper
from .gui_interface import PDFCompressorGUI
from .cli_interface import PDFCompressorCLI
from .config import QUALITY_SETTINGS, TIMEOUT_SETTINGS, GUI_SETTINGS

__all__ = [
    'PerformanceTracker',
    'get_file_size',
    'calculate_timeout', 
    'safe_remove_file',
    'create_temp_file',
    'compress_single_pdf',
    'check_ghostscript',
    'compress_directory',
    'compress_single_file_wrapper',
    'PDFCompressorGUI',
    'PDFCompressorCLI',
    'QUALITY_SETTINGS',
    'TIMEOUT_SETTINGS',
    'GUI_SETTINGS'
]