import subprocess
import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import glob
from datetime import datetime
import sys
import io
import logging
import shutil
import tempfile
from pathlib import Path

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
logger = logging.getLogger(__name__)

class PerformanceTracker:
    """Enhanced performance tracker with better metrics and logging"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.file_times = {}
        self.phase_times = {}
        self.failed_files = []
        self.successful_files = []
        
    def start_tracking(self, operation_name="Operation"):
        """Start timing an operation"""
        self.start_time = time.time()
        self.operation_name = operation_name
        self.failed_files = []
        self.successful_files = []
        timestamp = datetime.now().strftime('%H:%M:%S')
        message = f"⏱️ Starting {operation_name} at {timestamp}"
        print(message)
        logger.info(message)
        
    def track_phase(self, phase_name):
        """Track time for a specific phase"""
        current_time = time.time()
        if hasattr(self, '_last_phase_time'):
            phase_duration = current_time - self._last_phase_time
            self.phase_times[self._last_phase_name] = phase_duration
            logger.debug(f"Phase '{self._last_phase_name}' completed in {phase_duration:.2f}s")
        self._last_phase_time = current_time
        self._last_phase_name = phase_name
        
    def track_file(self, filename, file_start_time, success=True):
        """Track time for individual file processing"""
        file_duration = time.time() - file_start_time
        self.file_times[filename] = file_duration
        
        if success:
            self.successful_files.append(filename)
            logger.info(f"✅ Successfully processed: {os.path.basename(filename)} ({file_duration:.2f}s)")
        else:
            self.failed_files.append(filename)
            logger.error(f"❌ Failed to process: {os.path.basename(filename)} ({file_duration:.2f}s)")
        
    def end_tracking(self):
        """End timing and calculate total duration"""
        self.end_time = time.time()
        total_duration = self.end_time - self.start_time
        
        # Track final phase
        if hasattr(self, '_last_phase_time'):
            phase_duration = self.end_time - self._last_phase_time
            self.phase_times[self._last_phase_name] = phase_duration
            
        message = f"⏱️ {self.operation_name} completed in {total_duration:.2f} seconds"
        print(message)
        logger.info(message)
        logger.info(f"Success rate: {len(self.successful_files)}/{len(self.successful_files) + len(self.failed_files)} files")
        
        return total_duration
        
    def get_detailed_report(self):
        """Generate detailed performance report"""
        total_duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        
        report = f"📊 Performance Report:\n"
        report += f"⏱️ Total Duration: {total_duration:.2f} seconds\n"
        report += f"✅ Successful: {len(self.successful_files)} files\n"
        report += f"❌ Failed: {len(self.failed_files)} files\n"
        
        if self.phase_times:
            report += f"\n🔄 Phase Breakdown:\n"
            for phase, duration in self.phase_times.items():
                percentage = (duration / total_duration * 100) if total_duration > 0 else 0
                report += f"  • {phase}: {duration:.2f}s ({percentage:.1f}%)\n"
        
        if self.file_times:
            report += f"\n📄 File Processing Times:\n"
            sorted_files = sorted(self.file_times.items(), key=lambda x: x[1], reverse=True)
            for filename, duration in sorted_files[:5]:  # Show top 5 slowest files
                report += f"  • {os.path.basename(filename)}: {duration:.2f}s\n"
            
            if len(sorted_files) > 5:
                report += f"  ... and {len(sorted_files) - 5} more files\n"
                
            avg_time = sum(self.file_times.values()) / len(self.file_times)
            report += f"\n📈 Average per file: {avg_time:.2f}s\n"
            report += f"🐌 Slowest file: {max(self.file_times.values()):.2f}s\n"
            report += f"⚡ Fastest file: {min(self.file_times.values()):.2f}s\n"
        
        if self.failed_files:
            report += f"\n❌ Failed Files:\n"
            for failed_file in self.failed_files:
                report += f"  • {os.path.basename(failed_file)}\n"
        
        return report

# Global performance tracker
perf_tracker = PerformanceTracker()

def safe_remove_file(file_path, max_attempts=3):
    """Safely remove a file with retry mechanism"""
    for attempt in range(max_attempts):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Successfully removed: {file_path}")
                return True
        except PermissionError as e:
            logger.warning(f"Attempt {attempt + 1}/{max_attempts} failed to remove {file_path}: {e}")
            if attempt < max_attempts - 1:
                time.sleep(0.5)  # Wait before retry
            else:
                logger.error(f"Failed to remove {file_path} after {max_attempts} attempts")
                return False
        except Exception as e:
            logger.error(f"Unexpected error removing {file_path}: {e}")
            return False
    return False

def create_temp_file(base_path):
    """Create a temporary file in the same directory as the base file"""
    directory = os.path.dirname(base_path)
    basename = os.path.basename(base_path)
    name, ext = os.path.splitext(basename)
    
    # Create temporary file with unique name
    temp_fd, temp_path = tempfile.mkstemp(
        suffix=f"_compress{ext}",
        prefix=f"{name}_",
        dir=directory
    )
    os.close(temp_fd)  # Close the file descriptor
    return temp_path

def compress_single_pdf(input_file, output_file, quality_mode="balanced"):
    """Compress a single PDF file with improved error handling and temp file management"""
    file_start_time = time.time()
    
    if not os.path.exists(input_file):
        error_msg = f"❌ File not found: '{input_file}'"
        logger.error(error_msg)
        return False, error_msg

    # Create temporary file for processing
    temp_output_file = None
    try:
        temp_output_file = create_temp_file(output_file)
        logger.debug(f"Created temp file: {temp_output_file}")
        
        # Quality presets for scanned documents
        quality_settings = {
            "high": {
                "dpi": 300,
                "jpeg_quality": 85,
                "pdfsettings": "/prepress"
            },
            "balanced": {
                "dpi": 200,
                "jpeg_quality": 70,
                "pdfsettings": "/ebook"
            },
            "compact": {
                "dpi": 150,
                "jpeg_quality": 60,
                "pdfsettings": "/screen"
            }
        }
        
        settings = quality_settings.get(quality_mode, quality_settings["balanced"])
        logger.info(f"Using quality settings: {quality_mode} ({settings['dpi']}dpi)")

        command = [
            "gswin64c",
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            f"-dPDFSETTINGS={settings['pdfsettings']}",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            "-dSAFER",
            
            # A4 page settings
            "-sPAPERSIZE=a4",
            "-dFIXEDMEDIA",
            "-dPDFFitPage",
            "-dAutoRotatePages=/None",
            
            # B&W conversion settings
            "-sColorConversionStrategy=Gray",
            "-dProcessColorModel=/DeviceGray",
            "-dConvertCMYKImagesToRGB=false",
            
            # Image compression settings optimized for scanned documents
            "-dDownsampleColorImages=true",
            "-dDownsampleGrayImages=true",
            "-dDownsampleMonoImages=false",
            
            # Downsampling methods
            "-dColorImageDownsampleType=/Bicubic",
            "-dGrayImageDownsampleType=/Bicubic",
            "-dMonoImageDownsampleType=/Subsample",
            
            # Resolution settings
            f"-dColorImageResolution={settings['dpi']}",
            f"-dGrayImageResolution={settings['dpi']}",
            "-dMonoImageResolution=600",
            
            # Compression filters
            "-dAutoFilterColorImages=false",
            "-dAutoFilterGrayImages=false",
            "-dColorImageFilter=/DCTEncode",
            "-dGrayImageFilter=/DCTEncode",
            "-dMonoImageFilter=/CCITTFaxEncode",
            
            # JPEG quality
            f"-dJPEGQ={settings['jpeg_quality']}",
            
            # Additional optimization for scanned documents
            "-dDetectDuplicateImages=true",
            "-dCompressFonts=true",
            "-dSubsetFonts=true",
            "-dCompressPages=true",
            "-dUseFlateCompression=true",
            
            # Output file
            "-sOutputFile=" + temp_output_file,
            input_file
        ]

        # Log the command for debugging
        logger.debug(f"Ghostscript command: {' '.join(command)}")

        # Track Ghostscript execution time
        gs_start_time = time.time()
        result = subprocess.run(command, capture_output=True, text=True, timeout=300)  # 5 minute timeout
        gs_duration = time.time() - gs_start_time
        
        if result.returncode != 0:
            error_msg = f"❌ Ghostscript error (code {result.returncode}): {result.stderr}"
            logger.error(error_msg)
            logger.error(f"Ghostscript stdout: {result.stdout}")
            
            # Clean up temp file
            safe_remove_file(temp_output_file)
            perf_tracker.track_file(input_file, file_start_time, success=False)
            return False, error_msg
        
        # Check if output file was created and is valid
        if not os.path.exists(temp_output_file) or os.path.getsize(temp_output_file) == 0:
            error_msg = f"❌ Output file not created or empty: {temp_output_file}"
            logger.error(error_msg)
            safe_remove_file(temp_output_file)
            perf_tracker.track_file(input_file, file_start_time, success=False)
            return False, error_msg
        
        # Remove existing output file if it exists
        safe_remove_file(output_file)
        
        # Move temp file to final location
        try:
            shutil.move(temp_output_file, output_file)
            logger.info(f"Successfully moved temp file to: {output_file}")
        except Exception as e:
            error_msg = f"❌ Failed to move temp file to final location: {e}"
            logger.error(error_msg)
            safe_remove_file(temp_output_file)
            perf_tracker.track_file(input_file, file_start_time, success=False)
            return False, error_msg
        
        # Track successful file processing
        perf_tracker.track_file(input_file, file_start_time, success=True)
        
        # Log detailed timing info
        file_duration = time.time() - file_start_time
        logger.info(f"📄 {os.path.basename(input_file)}: {file_duration:.2f}s (GS: {gs_duration:.2f}s)")
        
        return True, "✅ Compression successful"
        
    except subprocess.TimeoutExpired:
        error_msg = f"❌ Ghostscript timeout (>5 minutes) for file: {input_file}"
        logger.error(error_msg)
        if temp_output_file:
            safe_remove_file(temp_output_file)
        perf_tracker.track_file(input_file, file_start_time, success=False)
        return False, error_msg
        
    except Exception as e:
        error_msg = f"❌ Unexpected error processing {input_file}: {e}"
        logger.error(error_msg)
        if temp_output_file:
            safe_remove_file(temp_output_file)
        perf_tracker.track_file(input_file, file_start_time, success=False)
        return False, error_msg

def compress_pdf():
    """Main compression function that handles both single files and directories"""
    input_path = input_entry.get().strip()
    quality_mode = quality_var.get()
    
    if not input_path:
        messagebox.showwarning("Empty Field", "Please select a PDF file or directory.")
        return

    if not os.path.exists(input_path):
        error_msg = f"❌ Path not found: '{input_path}'"
        messagebox.showerror("Error", error_msg)
        logger.error(error_msg)
        return

    # Check if Ghostscript is available
    try:
        subprocess.run(["gswin64c", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        error_msg = "❌ Ghostscript not found. Please install Ghostscript first."
        messagebox.showerror("Error", error_msg)
        logger.error(error_msg)
        return

    result_label.config(text="🔄 Compression in progress...")
    root.update()
    
    threading.Thread(target=process_compression, args=(input_path, quality_mode), daemon=True).start()

def process_compression(input_path, quality_mode):
    """Process compression in a separate thread"""
    try:
        # Start performance tracking
        if os.path.isfile(input_path):
            perf_tracker.start_tracking("Single File Compression")
        else:
            perf_tracker.start_tracking("Batch Compression")
        
        perf_tracker.track_phase("Initialization")
        
        if os.path.isfile(input_path):
            # Single PDF file
            compress_single_file_gui(input_path, quality_mode)
        elif os.path.isdir(input_path):
            # Directory with PDFs
            compress_directory(input_path, quality_mode)
        else:
            error_msg = "❌ Unsupported file type."
            result_label.config(text=error_msg)
            logger.error(error_msg)
            
    except Exception as e:
        error_msg = f"❌ Unexpected error in compression process: {e}"
        result_label.config(text=error_msg)
        logger.error(error_msg)

def compress_single_file_gui(input_file, quality_mode):
    """Compress a single PDF file (GUI version)"""
    perf_tracker.track_phase("File Processing")
    
    base_name = os.path.splitext(input_file)[0]
    output_file = f"{base_name}_optimized_bw.pdf"
    
    success, message = compress_single_pdf(input_file, output_file, quality_mode)
    
    perf_tracker.track_phase("Finalizing")
    total_duration = perf_tracker.end_tracking()
    
    if success:
        original_size = os.path.getsize(input_file)
        compressed_size = os.path.getsize(output_file)
        gain = ((original_size - compressed_size) / original_size) * 100
        
        processing_speed = original_size / (1024 * 1024) / total_duration  # MB/s
        
        result_text = (
            f"✅ Completed in {total_duration:.2f} sec\n"
            f"📄 Original size: {original_size / 1024 / 1024:.2f} MB\n"
            f"📉 Compressed size: {compressed_size / 1024 / 1024:.2f} MB\n"
            f"💾 Space saved: {gain:.1f}%\n"
            f"⚡ Processing speed: {processing_speed:.2f} MB/s\n"
            f"⚙️ Quality: {quality_mode.upper()}\n"
            f"📁 Output file: {os.path.basename(output_file)}\n\n"
            f"{perf_tracker.get_detailed_report()}"
        )
        result_label.config(text=result_text)
        logger.info(f"✅ File compressed successfully: {output_file}")
    else:
        result_label.config(text=f"❌ Compression failed: {message}")
        logger.error(f"❌ Compression failed: {message}")

def compress_directory(input_dir, quality_mode):
    """Compress all PDF files in a directory"""
    perf_tracker.track_phase("Directory Scanning")
    
    # Find all PDF files in the directory
    pdf_files = glob.glob(os.path.join(input_dir, "*.pdf"))
    
    if not pdf_files:
        error_msg = "❌ No PDF files found in the directory."
        result_label.config(text=error_msg)
        logger.warning(error_msg)
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    perf_tracker.track_phase("Directory Creation")
    
    # Create output directory
    output_dir = f"{input_dir}_optimized_bw"
    try:
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")
    except Exception as e:
        error_msg = f"❌ Failed to create output directory: {e}"
        result_label.config(text=error_msg)
        logger.error(error_msg)
        return
    
    perf_tracker.track_phase("Batch Processing")
    
    total_files = len(pdf_files)
    successful_compressions = 0
    total_original_size = 0
    total_compressed_size = 0
    
    for i, pdf_file in enumerate(pdf_files, 1):
        # Update progress with time estimate
        elapsed = time.time() - perf_tracker.start_time
        avg_time_per_file = elapsed / i if i > 0 else 0
        estimated_remaining = avg_time_per_file * (total_files - i)
        
        progress_text = (
            f"🔄 Processing {i}/{total_files}: {os.path.basename(pdf_file)}\n"
            f"⏱️ Elapsed: {elapsed:.1f}s | Estimated remaining: {estimated_remaining:.1f}s\n"
            f"✅ Successful: {successful_compressions} | ❌ Failed: {i - 1 - successful_compressions}"
        )
        result_label.config(text=progress_text)
        root.update()
        
        # Create output filename in the new directory
        filename = os.path.basename(pdf_file)
        base_name = os.path.splitext(filename)[0]
        output_file = os.path.join(output_dir, f"{base_name}_optimized_bw.pdf")
        
        success, message = compress_single_pdf(pdf_file, output_file, quality_mode)
        
        if success:
            successful_compressions += 1
            total_original_size += os.path.getsize(pdf_file)
            total_compressed_size += os.path.getsize(output_file)
            logger.info(f"✅ Compressed: {filename}")
        else:
            logger.error(f"❌ Failed: {filename} - {message}")
    
    perf_tracker.track_phase("Finalizing")
    total_duration = perf_tracker.end_tracking()
    
    # Final results with detailed metrics
    if successful_compressions > 0:
        total_gain = ((total_original_size - total_compressed_size) / total_original_size) * 100
        total_mb_processed = total_original_size / (1024 * 1024)
        processing_speed = total_mb_processed / total_duration
        avg_time_per_file = total_duration / successful_compressions
        
        result_text = (
            f"✅ Completed in {total_duration:.2f} sec\n"
            f"📁 Files processed: {successful_compressions}/{total_files}\n"
            f"📄 Total original size: {total_original_size / 1024 / 1024:.2f} MB\n"
            f"📉 Total compressed size: {total_compressed_size / 1024 / 1024:.2f} MB\n"
            f"💾 Total space saved: {total_gain:.1f}%\n"
            f"⚡ Overall speed: {processing_speed:.2f} MB/s\n"
            f"📊 Average time per file: {avg_time_per_file:.2f}s\n"
            f"⚙️ Quality: {quality_mode.upper()}\n"
            f"📁 Output directory: {os.path.basename(output_dir)}\n\n"
            f"{perf_tracker.get_detailed_report()}"
        )
        
        result_label.config(text=result_text)
        logger.info(f"✅ Batch compression completed: {output_dir}")
    else:
        error_msg = "❌ No files could be compressed successfully."
        result_label.config(text=error_msg)
        logger.error(error_msg)

def browse_input():
    """Browse for input file or directory"""
    choice = messagebox.askyesnocancel(
        "Selection Type",
        "What would you like to select:\n"
        "• YES = Single PDF file\n"
        "• NO = Directory containing PDFs\n"
        "• CANCEL = Cancel"
    )
    
    if choice is True:
        # Select single PDF file
        file_path = filedialog.askopenfilename(
            title="Select PDF File",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        if file_path:
            input_entry.delete(0, tk.END)
            input_entry.insert(0, file_path)
    elif choice is False:
        # Select directory
        dir_path = filedialog.askdirectory(
            title="Select Directory Containing PDFs"
        )
        if dir_path:
            input_entry.delete(0, tk.END)
            input_entry.insert(0, dir_path)

def open_log_file():
    """Open the log file in the default text editor"""
    log_file = "pdf_compressor.log"
    if os.path.exists(log_file):
        try:
            if sys.platform == "win32":
                os.startfile(log_file)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", log_file])
            else:  # Linux
                subprocess.run(["xdg-open", log_file])
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open log file: {e}")
    else:
        messagebox.showinfo("Info", "Log file not found.")

def clear_results():
    """Clear the results display"""
    result_label.config(text="")

# Enhanced GUI Interface
root = tk.Tk()
root.title("🔧 Enhanced PDF B&W Compressor with Advanced Logging")
root.geometry("900x700")
root.configure(bg="#f0f8ff")

# Configure styles
style = ttk.Style()
style.theme_use("clam")
style.configure("TButton", font=("Segoe UI", 10), padding=6)
style.configure("TLabel", font=("Segoe UI", 10), background="#f0f8ff")
style.configure("Title.TLabel", font=("Segoe UI", 12, "bold"), background="#f0f8ff")

# Main frame
main_frame = ttk.Frame(root, padding=20)
main_frame.pack(fill="both", expand=True)

# Title
title_label = ttk.Label(
    main_frame,
    text="🔧 Enhanced PDF B&W Compressor",
    style="Title.TLabel"
)
title_label.grid(row=0, column=0, columnspan=4, pady=(0, 10))

# Instructions
instructions = ttk.Label(
    main_frame,
    text="📝 Advanced PDF compression with comprehensive logging and error handling",
    font=("Segoe UI", 9, "italic")
)
instructions.grid(row=1, column=0, columnspan=4, pady=(0, 15))

# Input selection frame
input_frame = ttk.LabelFrame(main_frame, text="📥 Input Selection", padding=10)
input_frame.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(0, 10))

ttk.Label(input_frame, text="File or Directory:").grid(row=0, column=0, sticky="w")
input_entry = ttk.Entry(input_frame, width=70)
input_entry.grid(row=1, column=0, columnspan=2, padx=(0, 10), pady=5, sticky="ew")
ttk.Button(input_frame, text="Browse...", command=browse_input).grid(row=1, column=2)

# Quality selection frame
quality_frame = ttk.LabelFrame(main_frame, text="⚙️ Quality Settings", padding=10)
quality_frame.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(0, 10))

quality_var = tk.StringVar(value="balanced")
ttk.Radiobutton(quality_frame, text="📖 High Quality (300dpi) - Best for archival", 
                variable=quality_var, value="high").grid(row=0, column=0, sticky="w")
ttk.Radiobutton(quality_frame, text="⚖️ Balanced (200dpi) - Recommended for most uses", 
                variable=quality_var, value="balanced").grid(row=1, column=0, sticky="w")
ttk.Radiobutton(quality_frame, text="📦 Compact (150dpi) - Smallest file size", 
                variable=quality_var, value="compact").grid(row=2, column=0, sticky="w")

# Control buttons frame
control_frame = ttk.Frame(main_frame)
control_frame.grid(row=4, column=0, columnspan=4, pady=15)

ttk.Button(control_frame, text="🚀 Start Compression", command=compress_pdf).grid(row=0, column=0, padx=5)
ttk.Button(control_frame, text="📄 View Log", command=open_log_file).grid(row=0, column=1, padx=5)
ttk.Button(control_frame, text="🧹 Clear Results", command=clear_results).grid(row=0, column=2, padx=5)

# Results frame
results_frame = ttk.LabelFrame(main_frame, text="📊 Results & Progress", padding=10)
results_frame.grid(row=5, column=0, columnspan=4, sticky="nsew", pady=(0, 10))

# Configure scrollable text widget
result_text = tk.Text(results_frame, height=20, width=90, font=("Consolas", 9), wrap=tk.WORD)
scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=result_text.yview)
result_text.configure(yscrollcommand=scrollbar.set)

result_text.grid(row=0, column=0, sticky="nsew")
scrollbar.grid(row=0, column=1, sticky="ns")

# Configure grid weights
main_frame.grid_rowconfigure(5, weight=1)
main_frame.grid_columnconfigure(0, weight=1)
results_frame.grid_rowconfigure(0, weight=1)
results_frame.grid_columnconfigure(0, weight=1)
input_frame.grid_columnconfigure(0, weight=1)

# Create a label-like interface for the text widget
class ResultLabel:
    def __init__(self, text_widget):
        self.text_widget = text_widget
    
    def config(self, text=""):
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.insert(1.0, text)
        self.text_widget.see(tk.END)

result_label = ResultLabel(result_text)

# Footer info
footer_frame = ttk.Frame(main_frame)
footer_frame.grid(row=6, column=0, columnspan=4, pady=(10, 0))

info_text = (
    "💡 Enhanced Features: Advanced logging • Robust error handling • Temp file safety • "
    "Progress tracking • Performance metrics • CLI support"
)
info_label = ttk.Label(footer_frame, text=info_text, font=("Segoe UI", 8), justify="center")
info_label.pack()

def main_cli():
    """Enhanced CLI mode with better error handling"""
    
    if len(sys.argv) < 2:
        print("❌ Please provide a PDF file or directory path.")
        print("Usage: python script.py <path> [quality]")
        print("Quality options: high | balanced | compact (default: balanced)")
        print("\nExamples:")
        print("  python script.py document.pdf")
        print("  python script.py /path/to/pdfs/ balanced")
        print("  python script.py document.pdf high")
        return

    input_path = sys.argv[1]
    quality_mode = sys.argv[2] if len(sys.argv) > 2 else "balanced"
    
    # Validate quality mode
    if quality_mode not in ["high", "balanced", "compact"]:
        print(f"❌ Invalid quality mode: {quality_mode}")
        print("Valid options: high | balanced | compact")
        return

    if not os.path.exists(input_path):
        print(f"❌ Path not found: {input_path}")
        return

    # Check if Ghostscript is available
    try:
        result = subprocess.run(["gswin64c", "-version"], capture_output=True, check=True)
        gs_version = result.stdout.decode().strip().split('\n')[0]
        print(f"✅ Ghostscript found: {gs_version}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Ghostscript not found. Please install Ghostscript first.")
        print("Download from: https://www.ghostscript.com/download/gsdnld.html")
        return

    print(f"🔧 Starting PDF compression...")
    print(f"📁 Input: {input_path}")
    print(f"⚙️ Quality: {quality_mode}")
    print(f"📝 Log file: pdf_compressor.log")
    print("-" * 50)

    if os.path.isfile(input_path):
        # Single PDF file
        perf_tracker.start_tracking("Single File Compression (CLI)")
        compress_single_file_cli(input_path, quality_mode)
    elif os.path.isdir(input_path):
        # Directory with PDFs
        perf_tracker.start_tracking("Batch Compression (CLI)")
        compress_directory_cli(input_path, quality_mode)
    else:
        print("❌ Unsupported path type (neither file nor directory).")

def compress_single_file_cli(input_file, quality_mode):
    """Compress a single PDF file (CLI version)"""
    perf_tracker.track_phase("File Processing")
    
    base_name = os.path.splitext(input_file)[0]
    output_file = f"{base_name}_optimized_bw.pdf"
    
    print(f"🔄 Processing: {os.path.basename(input_file)}")
    
    success, message = compress_single_pdf(input_file, output_file, quality_mode)
    
    perf_tracker.track_phase("Finalizing")
    total_duration = perf_tracker.end_tracking()
    
    if success:
        original_size = os.path.getsize(input_file)
        compressed_size = os.path.getsize(output_file)
        gain = ((original_size - compressed_size) / original_size) * 100
        processing_speed = original_size / (1024 * 1024) / total_duration
        
        print(f"\n✅ Compression completed successfully!")
        print(f"📄 Original size: {original_size / 1024 / 1024:.2f} MB")
        print(f"📉 Compressed size: {compressed_size / 1024 / 1024:.2f} MB")
        print(f"💾 Space saved: {gain:.1f}%")
        print(f"⚡ Processing speed: {processing_speed:.2f} MB/s")
        print(f"📁 Output file: {output_file}")
        print(f"\n{perf_tracker.get_detailed_report()}")
    else:
        print(f"\n❌ Compression failed: {message}")
        print("📝 Check the log file for detailed error information.")

def compress_directory_cli(input_dir, quality_mode):
    """Compress all PDF files in a directory (CLI version)"""
    perf_tracker.track_phase("Directory Scanning")
    
    # Find all PDF files in the directory
    pdf_files = glob.glob(os.path.join(input_dir, "*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found in the directory.")
        return
    
    print(f"📁 Found {len(pdf_files)} PDF files to process")
    
    perf_tracker.track_phase("Directory Creation")
    
    # Create output directory
    output_dir = f"{input_dir}_optimized_bw"
    try:
        os.makedirs(output_dir, exist_ok=True)
        print(f"📁 Created output directory: {output_dir}")
    except Exception as e:
        print(f"❌ Failed to create output directory: {e}")
        return
    
    perf_tracker.track_phase("Batch Processing")
    
    total_files = len(pdf_files)
    successful_compressions = 0
    total_original_size = 0
    total_compressed_size = 0
    
    print(f"\n🔄 Processing {total_files} files...")
    print("-" * 50)
    
    for i, pdf_file in enumerate(pdf_files, 1):
        # Progress indicator
        elapsed = time.time() - perf_tracker.start_time
        avg_time_per_file = elapsed / i if i > 0 else 0
        estimated_remaining = avg_time_per_file * (total_files - i)
        
        print(f"📄 [{i}/{total_files}] {os.path.basename(pdf_file)}")
        print(f"⏱️  Elapsed: {elapsed:.1f}s | Est. remaining: {estimated_remaining:.1f}s")
        
        # Create output filename in the new directory
        filename = os.path.basename(pdf_file)
        base_name = os.path.splitext(filename)[0]
        output_file = os.path.join(output_dir, f"{base_name}_optimized_bw.pdf")
        
        success, message = compress_single_pdf(pdf_file, output_file, quality_mode)
        
        if success:
            successful_compressions += 1
            total_original_size += os.path.getsize(pdf_file)
            total_compressed_size += os.path.getsize(output_file)
            
            # Show compression stats for this file
            original_size = os.path.getsize(pdf_file)
            compressed_size = os.path.getsize(output_file)
            gain = ((original_size - compressed_size) / original_size) * 100
            print(f"✅ Compressed: {gain:.1f}% reduction ({original_size/1024/1024:.2f} → {compressed_size/1024/1024:.2f} MB)")
        else:
            print(f"❌ Failed: {message}")
        
        print("-" * 50)
    
    perf_tracker.track_phase("Finalizing")
    total_duration = perf_tracker.end_tracking()
    
    # Final results
    print(f"\n📊 BATCH COMPRESSION RESULTS")
    print("=" * 50)
    
    if successful_compressions > 0:
        total_gain = ((total_original_size - total_compressed_size) / total_original_size) * 100
        total_mb_processed = total_original_size / (1024 * 1024)
        processing_speed = total_mb_processed / total_duration
        avg_time_per_file = total_duration / successful_compressions
        
        print(f"✅ Successfully processed: {successful_compressions}/{total_files} files")
        print(f"⏱️  Total time: {total_duration:.2f} seconds")
        print(f"📄 Total original size: {total_original_size / 1024 / 1024:.2f} MB")
        print(f"📉 Total compressed size: {total_compressed_size / 1024 / 1024:.2f} MB")
        print(f"💾 Total space saved: {total_gain:.1f}%")
        print(f"⚡ Overall processing speed: {processing_speed:.2f} MB/s")
        print(f"📊 Average time per file: {avg_time_per_file:.2f}s")
        print(f"📁 Output directory: {output_dir}")
        
        print(f"\n{perf_tracker.get_detailed_report()}")
    else:
        print("❌ No files were successfully compressed.")
        print("📝 Check the log file for detailed error information.")

def show_help():
    """Show help information"""
    help_text = """
🔧 Enhanced PDF B&W Compressor Help

DESCRIPTION:
    This tool compresses PDF files to black & white with optimized settings
    for scanned documents. It provides comprehensive logging and error handling.

USAGE:
    GUI Mode:    python script.py
    CLI Mode:    python script.py <path> [quality]

ARGUMENTS:
    path        Path to PDF file or directory containing PDFs
    quality     Compression quality: high | balanced | compact (default: balanced)

QUALITY MODES:
    high        300dpi, 85% JPEG quality - Best for archival
    balanced    200dpi, 70% JPEG quality - Recommended for most uses  
    compact     150dpi, 60% JPEG quality - Smallest file size

EXAMPLES:
    python script.py document.pdf
    python script.py /path/to/pdfs/ balanced
    python script.py document.pdf high

REQUIREMENTS:
    - Python 3.6+
    - Ghostscript (gswin64c must be in PATH)
    - tkinter (for GUI mode)

LOGGING:
    All operations are logged to 'pdf_compressor.log' in the current directory.
    Use the 'View Log' button in GUI mode or check the file directly.

OUTPUT:
    - Single file: Creates <filename>_optimized_bw.pdf in same directory
    - Directory: Creates <dirname>_optimized_bw/ with all processed files
    """
    print(help_text)

if __name__ == "__main__":
    # Add help option
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        show_help()
    elif len(sys.argv) > 1:
        # CLI mode
        main_cli()
    else:
        # GUI mode
        try:
            print("🔧 Starting Enhanced PDF B&W Compressor...")
            print("📝 Log file: pdf_compressor.log")
            print("🖥️  GUI Mode - Opening interface...")
            root.mainloop()
        except Exception as e:
            print(f"❌ Failed to start GUI: {e}")
            print("📝 Try running in CLI mode: python script.py <path> [quality]")
            logger.error(f"GUI startup failed: {e}")