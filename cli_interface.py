import os
import sys
import logging
from batch_processor import compress_directory, compress_single_file_wrapper
from pdf_compressor import check_ghostscript
from performance_tracker import PerformanceTracker

logger = logging.getLogger(__name__)

class PDFCompressorCLI:
    def __init__(self):
        self.perf_tracker = PerformanceTracker()

    def show_help(self):
        """Show help information"""
        help_text = """
🔧 Enhanced PDF B&W Compressor Help

DESCRIPTION:
    This tool compresses PDF files to black & white with optimized settings
    for scanned documents. It provides comprehensive logging and error handling.

USAGE:
    GUI Mode:    python main.py
    CLI Mode:    python main.py <path> [quality]

ARGUMENTS:
    path        Path to PDF file or directory containing PDFs
    quality     Compression quality: high | balanced | compact (default: balanced)

QUALITY MODES:
    high        300dpi, 85% JPEG quality - Best for archival
    balanced    200dpi, 70% JPEG quality - Recommended for most uses  
    compact     150dpi, 60% JPEG quality - Smallest file size

EXAMPLES:
    python main.py document.pdf
    python main.py /path/to/pdfs/ balanced
    python main.py document.pdf high

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

    def run(self, args):
        """Main CLI entry point"""
        if len(args) < 2:
            print("❌ Please provide a PDF file or directory path.")
            print("Usage: python main.py <path> [quality]")
            print("Quality options: high | balanced | compact (default: balanced)")
            print("\nExamples:")
            print("  python main.py document.pdf")
            print("  python main.py /path/to/pdfs/ balanced")
            print("  python main.py document.pdf high")
            return

        # Check for help option
        if args[1] in ["-h", "--help", "help"]:
            self.show_help()
            return

        input_path = args[1]
        quality_mode = args[2] if len(args) > 2 else "balanced"
        
        # Validate quality mode
        if quality_mode not in ["high", "balanced", "compact"]:
            print(f"❌ Invalid quality mode: {quality_mode}")
            print("Valid options: high | balanced | compact")
            return

        if not os.path.exists(input_path):
            print(f"❌ Path not found: {input_path}")
            return

        # Check if Ghostscript is available
        gs_available, gs_message = check_ghostscript()
        if not gs_available:
            print(gs_message)
            print("Download from: https://www.ghostscript.com/download/gsdnld.html")
            return

        print(f"🔧 Starting PDF compression...")
        print(f"📁 Input: {input_path}")
        print(f"⚙️ Quality: {quality_mode}")
        print(f"📝 Log file: pdf_compressor.log")
        print("-" * 50)

        if os.path.isfile(input_path):
            # Single PDF file
            self.perf_tracker.start_tracking("Single File Compression (CLI)")
            self.compress_single_file_cli(input_path, quality_mode)
        elif os.path.isdir(input_path):
            # Directory with PDFs
            self.perf_tracker.start_tracking("Batch Compression (CLI)")
            self.compress_directory_cli(input_path, quality_mode)
        else:
            print("❌ Unsupported path type (neither file nor directory).")

    def compress_single_file_cli(self, input_file, quality_mode):
        """Compress a single PDF file (CLI version)"""
        print(f"🔄 Processing: {os.path.basename(input_file)}")
        
        success, message, results = compress_single_file_wrapper(
            input_file, quality_mode, self.perf_tracker
        )
        
        self.perf_tracker.track_phase("Finalizing")
        total_duration = self.perf_tracker.end_tracking()
        
        if success:
            original_size = results['total_original_size']
            compressed_size = results['total_compressed_size']
            gain = ((original_size - compressed_size) / original_size) * 100
            processing_speed = original_size / (1024 * 1024) / total_duration
            
            print(f"\n✅ Compression completed successfully!")
            print(f"📄 Original size: {original_size / 1024 / 1024:.2f} MB")
            print(f"📉 Compressed size: {compressed_size / 1024 / 1024:.2f} MB")
            print(f"💾 Space saved: {gain:.1f}%")
            print(f"⚡ Processing speed: {processing_speed:.2f} MB/s")
            print(f"📁 Output file: {results['output_file']}")
            print(f"\n{self.perf_tracker.get_detailed_report()}")
        else:
            print(f"\n❌ Compression failed: {message}")
            print("📝 Check the log file for detailed error information.")

    def compress_directory_cli(self, input_dir, quality_mode):
        """Compress all PDF files in a directory (CLI version)"""
        
        def progress_callback(message):
            """Print progress updates"""
            print(f"\r{message}", end="", flush=True)
        
        success, message, results = compress_directory(
            input_dir, quality_mode, self.perf_tracker, progress_callback
        )
        
        if not success:
            print(f"\n❌ {message}")
            return
        
        self.perf_tracker.track_phase("Finalizing")
        total_duration = self.perf_tracker.end_tracking()
        
        # Final results
        print(f"\n\n📊 BATCH COMPRESSION RESULTS")
        print("=" * 50)
        
        if results['successful_compressions'] > 0:
            total_gain = ((results['total_original_size'] - results['total_compressed_size']) / results['total_original_size']) * 100
            total_mb_processed = results['total_original_size'] / (1024 * 1024)
            processing_speed = total_mb_processed / total_duration
            avg_time_per_file = total_duration / results['successful_compressions']
            
            print(f"✅ Successfully processed: {results['successful_compressions']}/{results['total_files']} files")
            print(f"⏱️  Total time: {total_duration:.2f} seconds")
            print(f"📄 Total original size: {results['total_original_size'] / 1024 / 1024:.2f} MB")
            print(f"📉 Total compressed size: {results['total_compressed_size'] / 1024 / 1024:.2f} MB")
            print(f"💾 Total space saved: {total_gain:.1f}%")
            print(f"⚡ Overall processing speed: {processing_speed:.2f} MB/s")
            print(f"📊 Average time per file: {avg_time_per_file:.2f}s")
            print(f"📁 Output directory: {results['output_dir']}")
            
            print(f"\n{self.perf_tracker.get_detailed_report()}")
            
            if results['failed_files']:
                print(f"\n❌ Failed Files:")
                for filename, error in results['failed_files']:
                    print(f"  • {filename}: {error}")
        else:
            print("❌ No files were successfully compressed.")
            print("📝 Check the log file for detailed error information.")