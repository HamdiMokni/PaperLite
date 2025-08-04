import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
import sys
import subprocess
import logging
from batch_processor import compress_directory, compress_single_file_wrapper
from pdf_compressor import check_ghostscript
from performance_tracker import PerformanceTracker

logger = logging.getLogger(__name__)

class PDFCompressorGUI:
    def __init__(self, root):
        self.root = root
        self.perf_tracker = PerformanceTracker()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        self.root.title("🔧 Enhanced PDF B&W Compressor with Advanced Logging")
        self.root.geometry("900x700")
        self.root.configure(bg="#f0f8ff")

        # Configure styles
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("TLabel", font=("Segoe UI", 10), background="#f0f8ff")
        style.configure("Title.TLabel", font=("Segoe UI", 12, "bold"), background="#f0f8ff")

        # Main frame
        main_frame = ttk.Frame(self.root, padding=20)
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
        self.input_entry = ttk.Entry(input_frame, width=70)
        self.input_entry.grid(row=1, column=0, columnspan=2, padx=(0, 10), pady=5, sticky="ew")
        ttk.Button(input_frame, text="Browse...", command=self.browse_input).grid(row=1, column=2)

        # Quality selection frame
        quality_frame = ttk.LabelFrame(main_frame, text="⚙️ Quality Settings", padding=10)
        quality_frame.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(0, 10))

        self.quality_var = tk.StringVar(value="balanced")
        ttk.Radiobutton(quality_frame, text="📖 High Quality (300dpi) - Best for archival", 
                        variable=self.quality_var, value="high").grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(quality_frame, text="⚖️ Balanced (200dpi) - Recommended for most uses", 
                        variable=self.quality_var, value="balanced").grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(quality_frame, text="📦 Compact (150dpi) - Smallest file size", 
                        variable=self.quality_var, value="compact").grid(row=2, column=0, sticky="w")

        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=4, column=0, columnspan=4, pady=15)

        ttk.Button(control_frame, text="🚀 Start Compression", command=self.compress_pdf).grid(row=0, column=0, padx=5)
        ttk.Button(control_frame, text="📄 View Log", command=self.open_log_file).grid(row=0, column=1, padx=5)
        ttk.Button(control_frame, text="🧹 Clear Results", command=self.clear_results).grid(row=0, column=2, padx=5)

        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="📊 Results & Progress", padding=10)
        results_frame.grid(row=5, column=0, columnspan=4, sticky="nsew", pady=(0, 10))

        # Configure scrollable text widget
        self.result_text = tk.Text(results_frame, height=20, width=90, font=("Consolas", 9), wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)

        self.result_text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Configure grid weights
        main_frame.grid_rowconfigure(5, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        input_frame.grid_columnconfigure(0, weight=1)

        # Footer
        footer_frame = ttk.Frame(main_frame)
        footer_frame.grid(row=6, column=0, columnspan=4, pady=(10, 0))

        info_text = (
            "💡 Enhanced Features: Advanced logging • Robust error handling • Temp file safety • "
            "Progress tracking • Performance metrics • CLI support"
        )
        info_label = ttk.Label(footer_frame, text=info_text, font=("Segoe UI", 8), justify="center")
        info_label.pack()

    def update_result_text(self, text):
        """Update the result text widget"""
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(1.0, text)
        self.result_text.see(tk.END)
        self.root.update()

    def compress_pdf(self):
        """Main compression function that handles both single files and directories"""
        input_path = self.input_entry.get().strip()
        quality_mode = self.quality_var.get()
        
        if not input_path:
            messagebox.showwarning("Empty Field", "Please select a PDF file or directory.")
            return

        if not os.path.exists(input_path):
            error_msg = f"❌ Path not found: '{input_path}'"
            messagebox.showerror("Error", error_msg)
            logger.error(error_msg)
            return

        # Check if Ghostscript is available
        gs_available, gs_message = check_ghostscript()
        if not gs_available:
            messagebox.showerror("Error", gs_message)
            return

        self.update_result_text("🔄 Compression in progress...")
        
        threading.Thread(target=self.process_compression, args=(input_path, quality_mode), daemon=True).start()

    def process_compression(self, input_path, quality_mode):
        """Process compression in a separate thread"""
        try:
            # Start performance tracking
            if os.path.isfile(input_path):
                self.perf_tracker.start_tracking("Single File Compression")
            else:
                self.perf_tracker.start_tracking("Batch Compression")
            
            self.perf_tracker.track_phase("Initialization")
            
            if os.path.isfile(input_path):
                # Single PDF file
                self.compress_single_file_gui(input_path, quality_mode)
            elif os.path.isdir(input_path):
                # Directory with PDFs
                self.compress_directory_gui(input_path, quality_mode)
            else:
                error_msg = "❌ Unsupported file type."
                self.update_result_text(error_msg)
                logger.error(error_msg)
                
        except Exception as e:
            error_msg = f"❌ Unexpected error in compression process: {e}"
            self.update_result_text(error_msg)
            logger.error(error_msg)

    def compress_single_file_gui(self, input_file, quality_mode):
        """Compress a single PDF file (GUI version)"""
        success, message, results = compress_single_file_wrapper(
            input_file, quality_mode, self.perf_tracker, self.update_result_text
        )
        
        self.perf_tracker.track_phase("Finalizing")
        total_duration = self.perf_tracker.end_tracking()
        
        if success:
            original_size = results['total_original_size']
            compressed_size = results['total_compressed_size']
            gain = ((original_size - compressed_size) / original_size) * 100
            
            processing_speed = original_size / (1024 * 1024) / total_duration  # MB/s
            
            result_text = (
                f"✅ Completed in {total_duration:.2f} sec\n"
                f"📄 Original size: {original_size / 1024 / 1024:.2f} MB\n"
                f"📉 Compressed size: {compressed_size / 1024 / 1024:.2f} MB\n"
                f"💾 Space saved: {gain:.1f}%\n"
                f"⚡ Processing speed: {processing_speed:.2f} MB/s\n"
                f"⚙️ Quality: {quality_mode.upper()}\n"
                f"📁 Output file: {os.path.basename(results['output_file'])}\n\n"
                f"{self.perf_tracker.get_detailed_report()}"
            )
            self.update_result_text(result_text)
            logger.info(f"✅ File compressed successfully: {results['output_file']}")
        else:
            self.update_result_text(f"❌ Compression failed: {message}")
            logger.error(f"❌ Compression failed: {message}")

    def compress_directory_gui(self, input_dir, quality_mode):
        """Compress all PDF files in a directory (GUI version)"""
        success, message, results = compress_directory(
            input_dir, quality_mode, self.perf_tracker, self.update_result_text
        )
        
        if not success:
            self.update_result_text(f"❌ {message}")
            return
        
        self.perf_tracker.track_phase("Finalizing")
        total_duration = self.perf_tracker.end_tracking()
        
        # Final results with detailed metrics
        if results['successful_compressions'] > 0:
            total_gain = ((results['total_original_size'] - results['total_compressed_size']) / results['total_original_size']) * 100
            total_mb_processed = results['total_original_size'] / (1024 * 1024)
            processing_speed = total_mb_processed / total_duration
            avg_time_per_file = total_duration / results['successful_compressions']
            
            result_text = (
                f"✅ Completed in {total_duration:.2f} sec\n"
                f"📁 Files processed: {results['successful_compressions']}/{results['total_files']}\n"
                f"📄 Total original size: {results['total_original_size'] / 1024 / 1024:.2f} MB\n"
                f"📉 Total compressed size: {results['total_compressed_size'] / 1024 / 1024:.2f} MB\n"
                f"💾 Total space saved: {total_gain:.1f}%\n"
                f"⚡ Overall speed: {processing_speed:.2f} MB/s\n"
                f"📊 Average time per file: {avg_time_per_file:.2f}s\n"
                f"⚙️ Quality: {quality_mode.upper()}\n"
                f"📁 Output directory: {os.path.basename(results['output_dir'])}\n\n"
                f"{self.perf_tracker.get_detailed_report()}"
            )
            
            self.update_result_text(result_text)
            logger.info(f"✅ Batch compression completed: {results['output_dir']}")
        else:
            error_msg = "❌ No files could be compressed successfully."
            self.update_result_text(error_msg)
            logger.error(error_msg)

    def browse_input(self):
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
                self.input_entry.delete(0, tk.END)
                self.input_entry.insert(0, file_path)
        elif choice is False:
            # Select directory
            dir_path = filedialog.askdirectory(
                title="Select Directory Containing PDFs"
            )
            if dir_path:
                self.input_entry.delete(0, tk.END)
                self.input_entry.insert(0, dir_path)

    def open_log_file(self):
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
            
    def clear_results(self):
        """Clear the results display"""
        self.update_result_text("")