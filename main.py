import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path
from typing import List, Optional, Tuple
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import time
import traceback
import logging
from datetime import datetime
import json


def setup_logging():
    """Set up comprehensive logging system."""
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"pdf_processor_{timestamp}.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)  # Also log to console in CLI mode
        ]
    )
    
    # Create separate loggers for different components
    main_logger = logging.getLogger('PDFProcessor.Main')
    processor_logger = logging.getLogger('PDFProcessor.Core')
    gui_logger = logging.getLogger('PDFProcessor.GUI')
    
    main_logger.info(f"=== PDF Processor Session Started ===")
    main_logger.info(f"Log file: {log_file}")
    main_logger.info(f"Python version: {sys.version}")
    main_logger.info(f"Platform: {sys.platform}")
    main_logger.info(f"Working directory: {os.getcwd()}")
    
    return main_logger, processor_logger, gui_logger, log_file


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    logger = logging.getLogger('PDFProcessor.Main')
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        logger.debug(f"Running from PyInstaller bundle: {base_path}")
    except Exception:
        base_path = os.path.abspath(".")
        logger.debug(f"Running from source: {base_path}")
    
    full_path = os.path.join(base_path, relative_path)
    logger.debug(f"Resource path for '{relative_path}': {full_path}")
    return full_path


class PDFProcessor:
    """Main PDF processing class using Ghostscript."""

    def __init__(self, dpi: int = 200, paper_size: str = "a4", timeout: int = 600):
        self.logger = logging.getLogger('PDFProcessor.Core')
        self.dpi = dpi
        self.paper_size = paper_size.lower()
        self.timeout = timeout

        self.logger.info(
            f"Initializing PDFProcessor with DPI={dpi}, paper_size={paper_size}, timeout={timeout}s"
        )
        
        # Paper size mappings (width x height in points, 72 points = 1 inch)
        self.paper_sizes = {
            "a4": "595x842",
            "letter": "612x792", 
            "legal": "612x1008",
            "a3": "842x1191"
        }
        
        self.gs_command = self._find_ghostscript()
        self.logger.info(f"Ghostscript command: {self.gs_command}")
        
        # Statistics tracking
        self.stats = {
            'start_time': None,
            'end_time': None,
            'total_files': 0,
            'successful_files': 0,
            'failed_files': 0,
            'total_input_size': 0,
            'total_output_size': 0,
            'processing_times': [],
            'errors': []
        }
        
    def _find_ghostscript(self) -> str:
        """Find Ghostscript executable on the system."""
        self.logger.debug("Searching for Ghostscript executable")
        possible_commands = ["gs", "gswin64c", "gswin32c", "ghostscript"]
        
        # Check PATH first
        for cmd in possible_commands:
            path = shutil.which(cmd)
            if path:
                self.logger.info(f"Found Ghostscript in PATH: {path}")
                return cmd
        
        # Also check common installation paths on Windows
        if sys.platform == "win32":
            self.logger.debug("Checking common Windows installation paths")
            common_paths = [
                r"C:\Program Files\gs\gs*\bin\gswin64c.exe",
                r"C:\Program Files (x86)\gs\gs*\bin\gswin32c.exe",
                r"C:\gs\gs*\bin\gswin64c.exe",
                r"C:\gs\gs*\bin\gswin32c.exe"
            ]
            
            import glob
            for path_pattern in common_paths:
                self.logger.debug(f"Checking pattern: {path_pattern}")
                matches = glob.glob(path_pattern)
                if matches:
                    self.logger.info(f"Found Ghostscript at: {matches[0]}")
                    return matches[0]
        
        error_msg = (
            "Ghostscript not found. Please install Ghostscript and ensure it's in your PATH.\n\n"
            "Download from: https://www.ghostscript.com/download/gsdnld.html\n\n"
            "For Windows: Install the 64-bit version and make sure it's added to PATH,\n"
            "or install to default location (C:\\Program Files\\gs\\)"
        )
        self.logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    def _get_paper_size(self) -> str:
        """Get paper size string for Ghostscript."""
        size = self.paper_sizes.get(self.paper_size, self.paper_sizes["a4"])
        self.logger.debug(f"Paper size '{self.paper_size}' resolved to: {size}")
        return size
    
    def _get_file_size(self, file_path: Path) -> int:
        """Get file size in bytes."""
        try:
            size = file_path.stat().st_size
            self.logger.debug(f"File size for {file_path.name}: {size:,} bytes")
            return size
        except Exception as e:
            self.logger.warning(f"Could not get file size for {file_path}: {e}")
            return 0
    
    def _log_system_info(self):
        """Log system information for debugging."""
        try:
            import platform
            self.logger.info(f"System: {platform.system()} {platform.release()}")
            self.logger.info(f"Architecture: {platform.architecture()}")
            self.logger.info(f"Processor: {platform.processor()}")
            
            # Memory info (if available)
            try:
                import psutil
                memory = psutil.virtual_memory()
                self.logger.info(f"Total memory: {memory.total / (1024**3):.1f} GB")
                self.logger.info(f"Available memory: {memory.available / (1024**3):.1f} GB")
            except ImportError:
                self.logger.debug("psutil not available, skipping memory info")
        except Exception as e:
            self.logger.warning(f"Could not gather system info: {e}")
    
    def process_pdf(self, input_path: Path, output_path: Path, progress_callback=None) -> bool:
        """
        Process a single PDF file with Ghostscript.
        
        Args:
            input_path: Path to input PDF
            output_path: Path for output PDF
            progress_callback: Optional callback function for progress updates
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        self.logger.info(f"Starting processing: {input_path}")
        
        try:
            # Validate input file
            if not input_path.exists():
                raise FileNotFoundError(f"Input file does not exist: {input_path}")
            
            if not input_path.is_file():
                raise ValueError(f"Input path is not a file: {input_path}")
            
            input_size = self._get_file_size(input_path)
            self.stats['total_input_size'] += input_size
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Output directory created/verified: {output_path.parent}")
            
            # Build Ghostscript command
            paper_size = self._get_paper_size()
            
            cmd = [
                self.gs_command,
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.4",
                "-dColorConversionStrategy=/Gray",
                "-dProcessColorModel=/DeviceGray",
                "-dPDFSETTINGS=/ebook",
                f"-dPDFFitPage",
                f"-dFIXEDMEDIA",
                f"-dDEVICEWIDTHPOINTS={paper_size.split('x')[0]}",
                f"-dDEVICEHEIGHTPOINTS={paper_size.split('x')[1]}",
                f"-r{self.dpi}",
                "-dNOPAUSE",
                "-dQUIET", 
                "-dBATCH",
                f"-sOutputFile={str(output_path)}",
                str(input_path)
            ]
            
            self.logger.debug(f"Ghostscript command: {' '.join(cmd)}")
            
            if progress_callback:
                progress_callback(f"Processing: {input_path.name}")
            
            # Execute Ghostscript command
            self.logger.debug("Executing Ghostscript command")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            
            processing_time = time.time() - start_time
            self.stats['processing_times'].append(processing_time)
            
            self.logger.debug(f"Ghostscript return code: {result.returncode}")
            self.logger.debug(f"Processing time: {processing_time:.2f} seconds")
            
            if result.stdout:
                self.logger.debug(f"Ghostscript stdout: {result.stdout}")
            
            if result.returncode == 0:
                # Check if output file was created
                if output_path.exists():
                    output_size = self._get_file_size(output_path)
                    self.stats['total_output_size'] += output_size
                    
                    compression_ratio = (1 - output_size / input_size) * 100 if input_size > 0 else 0
                    
                    self.logger.info(f"✓ Successfully processed: {input_path.name}")
                    self.logger.info(f"  Input size: {input_size:,} bytes")
                    self.logger.info(f"  Output size: {output_size:,} bytes")
                    self.logger.info(f"  Compression: {compression_ratio:.1f}%")
                    self.logger.info(f"  Processing time: {processing_time:.2f}s")
                    
                    if progress_callback:
                        progress_callback(f"✓ Completed: {input_path.name} ({compression_ratio:.1f}% compressed)")
                    
                    self.stats['successful_files'] += 1
                    return True
                else:
                    error_msg = "Output file was not created"
                    self.logger.error(f"✗ Processing failed: {input_path.name} - {error_msg}")
                    self.stats['errors'].append({
                        'file': str(input_path),
                        'error': error_msg,
                        'timestamp': datetime.now().isoformat()
                    })
                    if progress_callback:
                        progress_callback(f"✗ Failed: {input_path.name} - {error_msg}")
                    self.stats['failed_files'] += 1
                    return False
            else:
                error_msg = result.stderr or result.stdout or "Unknown Ghostscript error"
                self.logger.error(f"✗ Ghostscript failed for {input_path.name}")
                self.logger.error(f"  Return code: {result.returncode}")
                self.logger.error(f"  Error output: {error_msg}")
                
                self.stats['errors'].append({
                    'file': str(input_path),
                    'error': f"Ghostscript error (code {result.returncode}): {error_msg}",
                    'timestamp': datetime.now().isoformat()
                })
                
                if progress_callback:
                    progress_callback(f"✗ Failed: {input_path.name} - {error_msg[:50]}...")
                
                self.stats['failed_files'] += 1
                return False
                
        except subprocess.TimeoutExpired:
            error_msg = f"Processing timeout after {self.timeout} seconds"
            self.logger.error(f"✗ Timeout: {input_path.name} - {error_msg}")
            self.stats['errors'].append({
                'file': str(input_path),
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            })
            if progress_callback:
                progress_callback(f"✗ Timeout: {input_path.name}")
            self.stats['failed_files'] += 1
            return False
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(f"✗ Exception processing {input_path.name}: {error_msg}")
            self.logger.error(f"  Exception type: {type(e).__name__}")
            self.logger.error(f"  Traceback: {traceback.format_exc()}")
            
            self.stats['errors'].append({
                'file': str(input_path),
                'error': error_msg,
                'exception_type': type(e).__name__,
                'traceback': traceback.format_exc(),
                'timestamp': datetime.now().isoformat()
            })
            
            if progress_callback:
                progress_callback(f"✗ Error: {input_path.name} - {str(e)[:50]}...")
            
            self.stats['failed_files'] += 1
            return False
    
    def process_batch(self, input_paths: List[Path], output_dir: Path, progress_callback=None) -> Tuple[int, int]:
        """
        Process multiple PDF files.
        
        Args:
            input_paths: List of input PDF paths
            output_dir: Output directory
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (successful_count, failed_count)
        """
        self.stats['start_time'] = datetime.now()
        self.stats['total_files'] = len(input_paths)
        
        self.logger.info(f"=== BATCH PROCESSING STARTED ===")
        self.logger.info(f"Total files to process: {len(input_paths)}")
        self.logger.info(f"Output directory: {output_dir}")
        self.logger.info(f"DPI: {self.dpi}, Paper size: {self.paper_size}")
        
        self._log_system_info()
        
        # Log all input files
        self.logger.info("Input files:")
        for i, path in enumerate(input_paths, 1):
            size = self._get_file_size(path)
            self.logger.info(f"  {i:2d}. {path.name} ({size:,} bytes)")
        
        successful = 0
        failed = 0
        total = len(input_paths)
        
        for i, input_path in enumerate(input_paths):
            self.logger.info(f"--- Processing file {i+1}/{total} ---")
            
            if progress_callback:
                progress_callback(f"Progress: {i+1}/{total} - {input_path.name}")
            
            # Generate output filename
            output_filename = f"compressed_{input_path.stem}.pdf"
            output_path = output_dir / output_filename
            
            self.logger.debug(f"Output path: {output_path}")
            
            if self.process_pdf(input_path, output_path, progress_callback):
                successful += 1
            else:
                failed += 1
            
            # Log progress
            self.logger.info(f"Progress: {i+1}/{total} completed (Success: {successful}, Failed: {failed})")
        
        self.stats['end_time'] = datetime.now()
        self.stats['successful_files'] = successful
        self.stats['failed_files'] = failed
        
        self._log_final_statistics()
        
        return successful, failed
    
    def _log_final_statistics(self):
        """Log comprehensive final statistics."""
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        self.logger.info("=== BATCH PROCESSING COMPLETED ===")
        self.logger.info(f"Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
        self.logger.info(f"Total files: {self.stats['total_files']}")
        self.logger.info(f"Successful: {self.stats['successful_files']}")
        self.logger.info(f"Failed: {self.stats['failed_files']}")
        self.logger.info(f"Success rate: {(self.stats['successful_files']/self.stats['total_files']*100):.1f}%")
        
        if self.stats['total_input_size'] > 0:
            self.logger.info(f"Total input size: {self.stats['total_input_size']:,} bytes ({self.stats['total_input_size']/(1024**2):.1f} MB)")
            self.logger.info(f"Total output size: {self.stats['total_output_size']:,} bytes ({self.stats['total_output_size']/(1024**2):.1f} MB)")
            overall_compression = (1 - self.stats['total_output_size'] / self.stats['total_input_size']) * 100
            self.logger.info(f"Overall compression: {overall_compression:.1f}%")
        
        if self.stats['processing_times']:
            avg_time = sum(self.stats['processing_times']) / len(self.stats['processing_times'])
            max_time = max(self.stats['processing_times'])
            min_time = min(self.stats['processing_times'])
            self.logger.info(f"Processing times - Avg: {avg_time:.2f}s, Min: {min_time:.2f}s, Max: {max_time:.2f}s")
        
        # Log errors summary
        if self.stats['errors']:
            self.logger.error(f"=== ERROR SUMMARY ({len(self.stats['errors'])} errors) ===")
            for error in self.stats['errors']:
                self.logger.error(f"File: {error['file']}")
                self.logger.error(f"Error: {error['error']}")
                self.logger.error(f"Time: {error['timestamp']}")
                if 'exception_type' in error:
                    self.logger.error(f"Exception type: {error['exception_type']}")
                self.logger.error("---")
        
        # Save statistics to JSON file
        try:
            stats_file = Path("logs") / f"processing_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Convert datetime objects to ISO format for JSON serialization
            json_stats = self.stats.copy()
            json_stats['start_time'] = self.stats['start_time'].isoformat() if self.stats['start_time'] else None
            json_stats['end_time'] = self.stats['end_time'].isoformat() if self.stats['end_time'] else None
            json_stats['duration_seconds'] = duration
            
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(json_stats, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Statistics saved to: {stats_file}")
        except Exception as e:
            self.logger.warning(f"Could not save statistics to JSON: {e}")


class PDFProcessorGUI:
    """GUI interface for PDF processing."""
    
    def __init__(self):
        self.logger = logging.getLogger('PDFProcessor.GUI')
        self.logger.info("Initializing GUI")
        
        self.root = tk.Tk()
        self.root.title("PDF Batch Processor v1.1 (Enhanced Logging)")
        self.root.geometry("650x500")
        
        # Set window icon if available
        try:
            icon_path = resource_path("icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
                self.logger.debug(f"Window icon set: {icon_path}")
        except Exception as e:
            self.logger.debug(f"Could not set window icon: {e}")
        
        # Center window on screen
        self.center_window()
        
        self.processor = None
        self.input_paths = []
        self.output_dir = None
        self.processing_thread = None
        
        self.setup_gui()
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.logger.info("GUI initialization completed")
        
    def center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.logger.debug(f"Window centered at {x},{y} with size {width}x{height}")
    
    def setup_gui(self):
        """Set up the GUI components."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="PDF Batch Processor v1.1", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 5))
        
        # Subtitle with logging info
        subtitle_label = ttk.Label(main_frame, text="Enhanced with comprehensive logging", font=("Arial", 9), foreground="gray")
        subtitle_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        # Configuration frame
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # DPI setting
        ttk.Label(config_frame, text="DPI:").grid(row=0, column=0, sticky=tk.W)
        self.dpi_var = tk.StringVar(value="200")
        dpi_combo = ttk.Combobox(config_frame, textvariable=self.dpi_var, values=["150", "200", "300", "600"], width=10, state="readonly")
        dpi_combo.grid(row=0, column=1, sticky=tk.W, padx=(5, 20))
        
        # Paper size setting
        ttk.Label(config_frame, text="Paper Size:").grid(row=0, column=2, sticky=tk.W)
        self.paper_var = tk.StringVar(value="a4")
        paper_combo = ttk.Combobox(config_frame, textvariable=self.paper_var, values=["a4", "letter", "legal", "a3"], width=10, state="readonly")
        paper_combo.grid(row=0, column=3, sticky=tk.W, padx=(5, 0))
        
        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="10")
        file_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(file_frame)
        button_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        ttk.Button(button_frame, text="Select PDF Files", command=self.select_files).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="Select Folder", command=self.select_folder).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(button_frame, text="Clear Selection", command=self.clear_selection).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(button_frame, text="View Logs", command=self.view_logs).grid(row=0, column=3)
        
        # Selected files display
        text_frame = ttk.Frame(file_frame)
        text_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        self.files_text = tk.Text(text_frame, height=6, width=70, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.files_text.yview)
        
        self.files_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.files_text.configure(yscrollcommand=scrollbar.set)
        
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.progress_var = tk.StringVar(value="Ready - Select PDF files to begin")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        self.progress_label.grid(row=0, column=0, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Process button
        self.process_button = ttk.Button(main_frame, text="Process PDFs", command=self.start_processing)
        self.process_button.grid(row=5, column=0, columnspan=2, pady=(0, 10))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        file_frame.columnconfigure(0, weight=1)
        file_frame.rowconfigure(1, weight=1)
        progress_frame.columnconfigure(0, weight=1)
        
        self.logger.debug("GUI setup completed")
    
    def view_logs(self):
        """Open the logs directory."""
        logs_dir = Path("logs")
        if logs_dir.exists():
            if sys.platform == "win32":
                os.startfile(logs_dir)
            elif sys.platform == "darwin":
                subprocess.run(["open", str(logs_dir)])
            else:
                subprocess.run(["xdg-open", str(logs_dir)])
            self.logger.info("Opened logs directory")
        else:
            messagebox.showinfo("No Logs", "No log files found. Logs will be created when processing starts.")
    
    def select_files(self):
        """Select individual PDF files."""
        self.logger.debug("User selecting individual files")
        files = filedialog.askopenfilenames(
            title="Select PDF files",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if files:
            self.input_paths = [Path(f) for f in files]
            self.output_dir = self.input_paths[0].parent / "compressed"
            self.update_files_display()
            self.status_var.set(f"Selected {len(files)} PDF file(s)")
            self.logger.info(f"User selected {len(files)} individual files")
            for file in files:
                self.logger.debug(f"Selected file: {file}")
    
    def select_folder(self):
        """Select a folder containing PDF files."""
        self.logger.debug("User selecting folder")
        folder = filedialog.askdirectory(title="Select folder containing PDFs")
        
        if folder:
            folder_path = Path(folder)
            pdf_files = list(folder_path.glob("*.pdf"))
            
            self.logger.info(f"Scanning folder: {folder}")
            self.logger.info(f"Found {len(pdf_files)} PDF files")
            
            if pdf_files:
                self.input_paths = pdf_files
                self.output_dir = folder_path / "compressed"
                self.update_files_display()
                self.status_var.set(f"Found {len(pdf_files)} PDF file(s) in folder")
                
                for file in pdf_files:
                    self.logger.debug(f"Found PDF: {file}")
            else:
                messagebox.showwarning("No PDFs Found", "No PDF files found in the selected folder.")
                self.status_var.set("No PDFs found in selected folder")
                self.logger.warning(f"No PDF files found in folder: {folder}")
    
    def clear_selection(self):
        """Clear file selection."""
        self.input_paths = []
        self.output_dir = None
        self.update_files_display()
        self.status_var.set("Selection cleared")
    
    def update_files_display(self):
        """Update the files display text widget."""
        self.files_text.delete(1.0, tk.END)
        
        if self.input_paths:
            self.files_text.insert(tk.END, f"Selected {len(self.input_paths)} PDF file(s):\n\n")
            for i, path in enumerate(self.input_paths, 1):
                self.files_text.insert(tk.END, f"{i:2d}. {path.name}\n")
            self.files_text.insert(tk.END, f"\nOutput folder: {self.output_dir}")
        else:
            self.files_text.insert(tk.END, "No files selected\n\n")
            self.files_text.insert(tk.END, "Click 'Select PDF Files' to choose individual files\n")
            self.files_text.insert(tk.END, "or 'Select Folder' to process all PDFs in a folder.")
    
    def update_progress(self, message):
        """Update progress display."""
        self.progress_var.set(message)
        self.root.update_idletasks()
    
    def start_processing(self):
        """Start PDF processing in a separate thread."""
        if not self.input_paths:
            messagebox.showwarning("No Files", "Please select PDF files or folder first.")
            return
        
        try:
            # Test Ghostscript availability
            dpi = int(self.dpi_var.get())
            paper_size = self.paper_var.get()
            test_processor = PDFProcessor(dpi=dpi, paper_size=paper_size, timeout=600)
            
        except Exception as e:
            messagebox.showerror("Ghostscript Error", str(e))
            return
        
        # Disable process button
        self.process_button.configure(state="disabled")
        self.progress_bar.start()
        self.status_var.set("Processing...")
        
        # Start processing thread
        thread = threading.Thread(target=self.process_pdfs_thread)
        thread.daemon = True
        thread.start()
    
    def process_pdfs_thread(self):
        """Process PDFs in background thread."""
        try:
            dpi = int(self.dpi_var.get())
            paper_size = self.paper_var.get()
            
            self.processor = PDFProcessor(dpi=dpi, paper_size=paper_size, timeout=600)
            
            successful, failed = self.processor.process_batch(
                self.input_paths,
                self.output_dir,
                progress_callback=self.update_progress
            )
            
            # Update UI on completion
            self.root.after(0, self.processing_completed, successful, failed)
            
        except Exception as e:
            error_msg = f"Processing error: {str(e)}"
            self.root.after(0, self.processing_error, error_msg)
    
    def processing_completed(self, successful, failed):
        """Handle processing completion."""
        self.progress_bar.stop()
        self.process_button.configure(state="normal")
        
        total = successful + failed
        message = f"Processing completed!\n\nTotal files: {total}\nSuccessful: {successful}\nFailed: {failed}"
        
        if failed == 0:
            messagebox.showinfo("Success", message + f"\n\nOutput folder: {self.output_dir}")
            self.status_var.set(f"Completed successfully - {successful} files processed")
        else:
            messagebox.showwarning("Completed with Errors", message)
            self.status_var.set(f"Completed with errors - {successful} successful, {failed} failed")
        
        self.progress_var.set("Ready - Select PDF files to begin")
    
    def processing_error(self, error_message):
        """Handle processing error."""
        self.progress_bar.stop()
        self.process_button.configure(state="normal")
        messagebox.showerror("Processing Error", error_message)
        self.progress_var.set("Ready - Error occurred")
        self.status_var.set("Error occurred during processing")
    
    def on_closing(self):
        """Handle application closing."""
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """Run the GUI application."""
        try:
            self.root.mainloop()
        except Exception as e:
            messagebox.showerror("Application Error", f"An unexpected error occurred:\n{str(e)}")


def cli_interface():
    """Command-line interface for PDF processing."""
    parser = argparse.ArgumentParser(description="Batch PDF processor using Ghostscript")
    parser.add_argument("input", help="Input PDF file or folder containing PDFs")
    parser.add_argument("-o", "--output", help="Output folder (default: creates 'compressed' folder)")
    parser.add_argument("-d", "--dpi", type=int, default=200, help="Output DPI (default: 200)")
    parser.add_argument("-p", "--paper", default="a4", choices=["a4", "letter", "legal", "a3"],
                       help="Paper size (default: a4)")
    parser.add_argument("-t", "--timeout", type=int, default=600, help="Ghostscript timeout in seconds (default: 600)")
    
    args = parser.parse_args()
    
    # Determine input paths
    input_path = Path(args.input)
    
    if input_path.is_file() and input_path.suffix.lower() == ".pdf":
        input_paths = [input_path]
        output_dir = input_path.parent / "compressed"
    elif input_path.is_dir():
        input_paths = list(input_path.glob("*.pdf"))
        output_dir = input_path / "compressed"
        if not input_paths:
            print("No PDF files found in the specified folder.")
            return 1
    else:
        print("Input must be a PDF file or folder containing PDFs.")
        return 1
    
    # Set output directory
    if args.output:
        output_dir = Path(args.output)
    
    print(f"PDF Batch Processor v1.0")
    print(f"Found {len(input_paths)} PDF file(s)")
    print(f"Output folder: {output_dir}")
    print(f"Settings: DPI={args.dpi}, Paper={args.paper}, Timeout={args.timeout}s")
    print("-" * 50)
    
    # Process files
    try:
        processor = PDFProcessor(dpi=args.dpi, paper_size=args.paper, timeout=args.timeout)
        
        def progress_callback(message):
            print(message)
        
        successful, failed = processor.process_batch(input_paths, output_dir, progress_callback)
        
        print("-" * 50)
        print(f"Processing completed!")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        
        return 0 if failed == 0 else 1
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


def main():
    """Main entry point."""
    main_logger, _, _, _ = setup_logging()
    main_logger.info("Application starting")
    # Set up exception handling for GUI mode
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        print(f"Unhandled exception: {error_msg}")
        
        if tk._default_root:
            messagebox.showerror("Unexpected Error", 
                               f"An unexpected error occurred:\n\n{exc_type.__name__}: {exc_value}")
    
    sys.excepthook = handle_exception
    
    if len(sys.argv) > 1:
        # CLI mode
        main_logger.info("Running in CLI mode")
        sys.exit(cli_interface())
    else:
        # GUI mode
        main_logger.info("Running in GUI mode")
        try:
            app = PDFProcessorGUI()
            app.run()
        except Exception as e:
            print(f"GUI Error: {e}")
            print("Usage: python pdf_processor.py <input_file_or_folder> [options]")


if __name__ == "__main__":
    main()
