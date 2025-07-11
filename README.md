# 🔧 Enhanced PDF B&W Compressor

A powerful Python tool for compressing PDF files to black & white with optimized settings for scanned documents. Features both GUI and CLI interfaces with comprehensive logging and error handling.

## ✨ Features

- **Dual Interface**: Both graphical (GUI) and command-line (CLI) modes
- **Batch Processing**: Compress single files or entire directories
- **Quality Presets**: Three compression levels optimized for different use cases
- **Advanced Logging**: Comprehensive error handling and performance tracking
- **Progress Tracking**: Real-time progress updates with time estimates
- **Detailed Reports**: File-by-file compression statistics and performance metrics
- **Robust Error Handling**: Graceful handling of corrupted files and processing errors
- **Temp File Safety**: Secure temporary file management to prevent data loss

## 🚀 Quick Start

### GUI Mode (Recommended for beginners)
```bash
python pdf_compressor.py
```

### CLI Mode
```bash
# Single file
python pdf_compressor.py document.pdf

# Directory with quality setting
python pdf_compressor.py /path/to/pdfs/ balanced

# High quality compression
python pdf_compressor.py document.pdf high
```

## 📋 Requirements

### System Requirements
- **Python 3.6+**
- **Ghostscript** (must be installed and accessible via `gswin64c` command)
- **tkinter** (usually included with Python, required for GUI mode)

### Python Dependencies
All dependencies are part of Python's standard library:
- `tkinter` - GUI interface
- `subprocess` - External command execution
- `threading` - Background processing
- `glob` - File pattern matching
- `logging` - Comprehensive logging
- `tempfile` - Safe temporary file handling

## 🛠️ Installation

1. **Install Python 3.6+**
   - Download from [python.org](https://www.python.org/downloads/)

2. **Install Ghostscript**
   - Download from [ghostscript.com](https://www.ghostscript.com/download/gsdnld.html)
   - Ensure `gswin64c` is in your system PATH

3. **Download the Script**
   ```bash
   # Save the script as pdf_compressor.py
   ```

4. **Verify Installation**
   ```bash
   python pdf_compressor.py --help
   ```

## ⚙️ Quality Settings

| Quality | DPI | JPEG Quality | Use Case | File Size |
|---------|-----|--------------|----------|-----------|
| **High** | 300 | 85% | Archival documents, fine text | Largest |
| **Balanced** | 200 | 70% | General use, good quality/size ratio | Medium |
| **Compact** | 150 | 60% | Maximum compression, web sharing | Smallest |

## 📖 Usage Examples

### GUI Mode
1. Launch the application: `python pdf_compressor.py`
2. Click "Browse..." to select a PDF file or directory
3. Choose your quality setting
4. Click "🚀 Start Compression"
5. Monitor progress in the results panel

### CLI Mode Examples

```bash
# Basic usage - single file with default quality
python pdf_compressor.py document.pdf

# Batch processing with balanced quality
python pdf_compressor.py ./documents/ balanced

# High quality single file
python pdf_compressor.py important_document.pdf high

# Compact compression for web sharing
python pdf_compressor.py ./web_docs/ compact

# Show help
python pdf_compressor.py --help
```

## 📁 Output Structure

### Single File Processing
```
original_document.pdf
original_document_optimized_bw.pdf  ← Compressed output
```

### Directory Processing
```
documents/
├── file1.pdf
├── file2.pdf
└── file3.pdf

documents_optimized_bw/  ← Output directory
├── file1_optimized_bw.pdf
├── file2_optimized_bw.pdf
└── file3_optimized_bw.pdf
```

## 📊 Performance Metrics

The tool provides detailed performance analytics:

- **Processing Speed**: MB/s throughput
- **Compression Ratios**: Space saved per file
- **Time Tracking**: Per-file and total processing times
- **Success Rates**: Files processed vs. failed
- **Phase Breakdown**: Time spent in each processing phase

## 📝 Logging

All operations are logged to `pdf_compressor.log` with:
- Timestamps for all operations
- Detailed error messages
- Performance metrics
- File processing status
- System information

### Log Levels
- **INFO**: General operation status
- **WARNING**: Non-critical issues
- **ERROR**: Processing failures
- **DEBUG**: Detailed technical information

## 🔧 Advanced Features

### Compression Optimizations
- **A4 Page Standardization**: Ensures consistent page sizes
- **Grayscale Conversion**: Converts all colors to black & white
- **Image Downsampling**: Reduces image resolution for smaller files
- **Font Compression**: Optimizes embedded fonts
- **Duplicate Detection**: Removes duplicate images

### Error Handling
- **Timeout Protection**: 5-minute timeout per file
- **Corrupted File Detection**: Skips unreadable files
- **Disk Space Monitoring**: Checks available space
- **Graceful Degradation**: Continues processing despite individual failures

### Performance Features
- **Parallel Processing**: Efficient CPU utilization
- **Progress Estimation**: Accurate time remaining calculations
- **Memory Management**: Efficient handling of large files
- **Temp File Safety**: Prevents data loss during processing

## 🐛 Troubleshooting

### Common Issues

**"Ghostscript not found"**
```bash
# Verify Ghostscript installation
gswin64c -version

# If not found, add to PATH or reinstall Ghostscript
```

**"Permission denied" errors**
```bash
# Ensure write permissions in output directory
# Close any PDFs that might be open in other applications
```

**"Processing timeout"**
```bash
# Large files may take longer than 5 minutes
# Check log file for specific error details
```

**GUI won't start**
```bash
# Try CLI mode instead
python pdf_compressor.py document.pdf

# Check if tkinter is properly installed
python -c "import tkinter; print('tkinter OK')"
```

### Performance Tips

1. **Close other applications** to free up system resources
2. **Use SSD storage** for faster file I/O
3. **Process smaller batches** for very large directories
4. **Monitor system resources** during batch operations

## 📄 License

This project is provided as-is for educational and personal use. Please ensure you have the right to modify and compress any PDF files you process.

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Additional compression algorithms
- More output formats
- Enhanced GUI features
- Performance optimizations
- Better error recovery

## 📞 Support

For issues and questions:
1. Check the log file (`pdf_compressor.log`) for detailed error information
2. Verify Ghostscript installation and PATH configuration
3. Ensure input files are valid PDF documents
4. Test with a small batch before processing large directories

## 🔄 Version History

- **v1.0**: Initial release with basic compression
- **v2.0**: Added GUI interface and batch processing
- **v3.0**: Enhanced logging and error handling
- **v4.0**: Performance tracking and advanced metrics
- **Current**: Comprehensive feature set with robust error handling

---