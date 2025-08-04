# 🔧 Enhanced PDF B&W Compressor

A comprehensive PDF compression tool that converts PDFs to black & white with optimized settings for scanned documents. Features both GUI and CLI interfaces with advanced logging, performance tracking, and robust error handling.

## ✨ Features

- **Dual Interface**: Both GUI and command-line interfaces
- **Advanced Compression**: Optimized settings for scanned documents
- **Quality Modes**: High, Balanced, and Compact compression options
- **Batch Processing**: Handle single files or entire directories
- **Performance Tracking**: Detailed metrics and timing information
- **Robust Error Handling**: Comprehensive logging and recovery mechanisms
- **Progress Monitoring**: Real-time progress updates and time estimates
- **Temp File Safety**: Secure temporary file handling
- **Cross-Platform**: Windows, Linux, and macOS support

## 📋 Requirements

- **Python 3.6+**
- **Ghostscript** (gswin64c must be in system PATH)
- **tkinter** (for GUI mode - usually included with Python)
- Minimum 4GB RAM recommended for large PDF processing
- Sufficient disk space for temporary files

## 🚀 Installation

1. **Install Python 3.6 or higher**
   
2. **Install Ghostscript**
   - Download from: https://www.ghostscript.com/download/gsdnld.html
   - Ensure `gswin64c` is available in your system PATH

3. **Download the application**
   ```bash
   git clone <repository-url>
   cd pdf-compressor
   ```

4. **Install dependencies** (optional for development)
   ```bash
   pip install -r requirements.txt
   ```

## 💻 Usage

### GUI Mode
```bash
python main.py
```

### CLI Mode

**Single file compression:**
```bash
python main.py document.pdf
python main.py document.pdf high
```

**Directory compression:**
```bash
python main.py /path/to/pdfs/
python main.py /path/to/pdfs/ balanced
```

**Help:**
```bash
python main.py --help
```

## ⚙️ Quality Modes

| Mode | DPI | JPEG Quality | Best For |
|------|-----|--------------|----------|
| **High** | 300 | 85% | Archival documents |
| **Balanced** | 200 | 70% | General use (recommended) |
| **Compact** | 150 | 60% | Smallest file size |

## 📁 File Structure

```
pdf-compressor/
├── main.py                 # Main entry point
├── config.py              # Configuration settings
├── performance_tracker.py  # Performance monitoring
├── file_utils.py          # File utility functions
├── pdf_compressor.py      # Core compression logic
├── batch_processor.py     # Batch processing functionality
├── gui_interface.py       # GUI implementation
├── cli_interface.py       # CLI implementation
├── __init__.py           # Package initialization
├── requirements.txt      # Dependencies
└── README.md            # This file
```

## 📊 Output

### Single File
- Creates `<filename>_optimized_bw.pdf` in the same directory

### Directory Processing
- Creates `<dirname>_optimized_bw/` directory
- All processed files are saved with `_optimized_bw` suffix

## 📝 Logging

All operations are logged to `pdf_compressor.log` in the current directory:
- Detailed processing information
- Error messages and stack traces
- Performance metrics
- File operation status

## 🎯 Examples

### Basic Usage
```bash
# Compress a single PDF with balanced quality
python main.py document.pdf

# Compress with high quality
python main.py important_document.pdf high

# Compress all PDFs in a directory
python main.py ./documents/ compact
```

### Advanced Examples
```bash
# Process a large directory with balanced settings
python main.py /home/user/scanned_docs/ balanced

# High-quality compression for archival
python main.py archive.pdf high
```

## 🔧 Configuration

The application uses several configuration files:

- **config.py**: Quality settings, timeouts, GUI parameters
- **Logging**: Automatic log file creation and rotation
- **Temp Files**: Secure temporary file handling in the same directory