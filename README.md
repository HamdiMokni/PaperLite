# PaperLite

PaperLite is a lightweight tool for compressing and standardising PDF files using Ghostscript. It includes a minimal Tkinter GUI and a command‑line interface.

## Features

- Batch processing of PDF files
- Optional grayscale conversion
- Standardised page sizes (A4, Letter, Legal, A3)
- DPI control for adjusting quality
- Automatic creation of an output folder

## Requirements

- Python 3.8+
- [Ghostscript](https://www.ghostscript.com/) available on your PATH
- `psutil` (optional, used for additional system information)

## Installation

Clone the repository and install the optional dependency:

```bash
git clone https://github.com/yourusername/paperlite.git
cd paperlite
pip install psutil
```

## Usage

### GUI

```bash
python main.py
```

### Command Line

```bash
python main.py <input_path> [-o OUTPUT] [-d DPI] [-p {a4,letter,legal,a3}] [-t TIMEOUT]
```

For example:

```bash
python main.py ./pdfs_to_compress -o ./compressed -d 150 -p a4
```

### Build an Executable

If you need a standalone executable, install PyInstaller and build:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

The resulting binary will be located in `dist/`.

## License

This project is released under the MIT License.

## Acknowledgements

Built with Python and Ghostscript.
