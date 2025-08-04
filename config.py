import os
import sys
import io
import logging

def setup_logging():
    """Setup logging configuration"""
    # Configure UTF-8 encoding
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('pdf_compressor.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

# Quality presets for scanned documents
QUALITY_SETTINGS = {
    "high": {
        "dpi": 300,
        "jpeg_quality": 85,
        "pdfsettings": "/prepress",
        "description": "Best for archival - 300dpi, 85% JPEG quality"
    },
    "balanced": {
        "dpi": 200,
        "jpeg_quality": 70,
        "pdfsettings": "/ebook",
        "description": "Recommended for most uses - 200dpi, 70% JPEG quality"
    },
    "compact": {
        "dpi": 150,
        "jpeg_quality": 60,
        "pdfsettings": "/screen",
        "description": "Smallest file size - 150dpi, 60% JPEG quality"
    }
}

# File size based timeout calculations
TIMEOUT_SETTINGS = {
    "base_timeout": 120,  # 2 minutes base
    "small_file_mb": 1,
    "medium_file_mb": 10,
    "large_file_mb": 50,
    "small_additional": 60,   # 1 minute
    "medium_additional": 180, # 3 minutes
    "large_additional": 600,  # 10 minutes
    "xlarge_additional": 1200 # 20 minutes
}

# Process monitoring settings
PROCESS_SETTINGS = {
    "poll_interval": 10,  # Check every 10 seconds
    "max_file_remove_attempts": 3,
    "file_remove_retry_delay": 0.5
}

# GUI settings
GUI_SETTINGS = {
    "window_title": "🔧 Enhanced PDF B&W Compressor with Advanced Logging",
    "window_size": "900x700",
    "background_color": "#f0f8ff",
    "font_family": "Segoe UI",
    "monospace_font": "Consolas"
}

# Output file naming patterns
OUTPUT_PATTERNS = {
    "single_file_suffix": "_optimized_bw",
    "directory_suffix": "_optimized_bw"
}