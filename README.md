# 📄 PaperLite

**PaperLite** is a lightweight desktop tool for batch processing and compressing PDF files using [Ghostscript](https://www.ghostscript.com/). It provides both a user-friendly graphical interface and a flexible command-line interface (CLI), allowing users to convert PDFs to grayscale, optimize file size, and standardize page dimensions with ease.

---

## ✨ Features

- ✅ Batch compress and convert multiple PDF files
- 🎨 Convert PDFs to grayscale for reduced file size
- 📄 Standardize paper size (A4, Letter, Legal, A3)
- ⚙️ Adjustable DPI settings for quality control
- 🖥️ Simple and intuitive GUI built with Tkinter
- 💻 Command-line support for automation
- 📁 Automatic output folder creation
- 🧩 Ghostscript integration (auto-detected)

---

## 🖥️ GUI Preview

![GUI Screenshot](screenshots/gui_sample.png) <!-- Replace with actual screenshot -->

---

## 🚀 Getting Started

### 📦 Requirements

- Python 3.8 or later
- [Ghostscript](https://www.ghostscript.com/download/gsdnld.html) (must be installed and added to your system's PATH)

### 📥 Installation

```bash
git clone https://github.com/yourusername/paperlite.git
cd paperlite
pip install -r requirements.txt
````

---

### ▶️ Run the Application

#### GUI Mode:

```bash
python main.py
```

#### CLI Mode:

```bash
python main.py <input_file_or_folder> [options]
```

**Example:**

```bash
python main.py ./pdfs_to_compress -o ./compressed -d 150 -p a4
```

---

### 🛠️ CLI Options

| Option           | Description                                | Default      |
| ---------------- | ------------------------------------------ | ------------ |
| `-o`, `--output` | Output folder for processed PDFs           | `compressed` |
| `-d`, `--dpi`    | DPI for rendering and compression          | `200`        |
| `-p`, `--paper`  | Paper size (`a4`, `letter`, `legal`, `a3`) | `a4`         |

---

## 🧊 Build Standalone Executable (with PyInstaller)

To generate a **single `.exe` file** for easy distribution (with no console window):

### 1. Install PyInstaller

```bash
pip install pyinstaller
```

### 2. Build the Executable

```bash
pyinstaller --onefile --windowed main.py
```

> ✅ `--onefile`: bundles everything into a single `.exe`
> ✅ `--windowed`: prevents a console window from opening when running the GUI (Windows only)

The output `.exe` file will be located in the `dist/` folder.

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

## 🙌 Acknowledgments

* Built with ❤️ using Python and Ghostscript
* Thanks to the open-source community behind PyInstaller, Tkinter, and cx\_Freeze
* Special thanks to users who contributed ideas and feedback

---
