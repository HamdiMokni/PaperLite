import os
import time
import glob
import logging
from pdf_compressor import compress_single_pdf
from file_utils import get_file_size

logger = logging.getLogger(__name__)

def compress_directory(input_dir, quality_mode, perf_tracker=None, progress_callback=None):
    """Compress all PDF files in a directory"""
    if perf_tracker:
        perf_tracker.track_phase("Directory Scanning")
    
    # Find all PDF files in the directory
    pdf_files = glob.glob(os.path.join(input_dir, "*.pdf"))
    
    if not pdf_files:
        error_msg = "❌ No PDF files found in the directory."
        logger.warning(error_msg)
        return False, error_msg, {}
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    # Sort files by size (process smaller files first)
    pdf_files.sort(key=get_file_size)
    
    if perf_tracker:
        perf_tracker.track_phase("Directory Creation")
    
    # Create output directory
    output_dir = f"{input_dir}_optimized_bw"
    try:
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")
    except Exception as e:
        error_msg = f"❌ Failed to create output directory: {e}"
        logger.error(error_msg)
        return False, error_msg, {}
    
    if perf_tracker:
        perf_tracker.track_phase("Batch Processing")
    
    total_files = len(pdf_files)
    successful_compressions = 0
    total_original_size = 0
    total_compressed_size = 0
    failed_files = []
    
    for i, pdf_file in enumerate(pdf_files, 1):
        # Update progress with time estimate
        elapsed = time.time() - perf_tracker.start_time if perf_tracker else 0
        avg_time_per_file = elapsed / i if i > 0 else 0
        estimated_remaining = avg_time_per_file * (total_files - i)
        
        file_size = get_file_size(pdf_file)
        progress_text = (
            f"🔄 Processing {i}/{total_files}: {os.path.basename(pdf_file)}\n"
            f"📏 File size: {file_size:.2f} MB\n"
            f"⏱️ Elapsed: {elapsed:.1f}s | Estimated remaining: {estimated_remaining:.1f}s\n"
            f"✅ Successful: {successful_compressions} | ❌ Failed: {i - 1 - successful_compressions}"
        )
        
        if progress_callback:
            progress_callback(progress_text)
        
        # Create output filename in the new directory
        filename = os.path.basename(pdf_file)
        base_name = os.path.splitext(filename)[0]
        output_file = os.path.join(output_dir, f"{base_name}_optimized_bw.pdf")
        
        def update_file_progress(message):
            """Update progress for current file"""
            current_progress = (
                f"🔄 Processing {i}/{total_files}: {os.path.basename(pdf_file)}\n"
                f"{message}\n"
                f"✅ Successful: {successful_compressions} | ❌ Failed: {i - 1 - successful_compressions}"
            )
            if progress_callback:
                progress_callback(current_progress)
        
        success, message = compress_single_pdf(
            pdf_file, output_file, quality_mode, 
            update_file_progress, perf_tracker
        )
        
        if success:
            successful_compressions += 1
            total_original_size += os.path.getsize(pdf_file)
            total_compressed_size += os.path.getsize(output_file)
            logger.info(f"✅ Compressed: {filename}")
        else:
            failed_files.append((filename, message))
            logger.error(f"❌ Failed: {filename} - {message}")
    
    # Prepare results
    results = {
        'total_files': total_files,
        'successful_compressions': successful_compressions,
        'failed_files': failed_files,
        'total_original_size': total_original_size,
        'total_compressed_size': total_compressed_size,
        'output_dir': output_dir
    }
    
    return True, "Batch processing completed", results

def compress_single_file_wrapper(input_file, quality_mode, perf_tracker=None, progress_callback=None):
    """Wrapper for single file compression with consistent interface"""
    if perf_tracker:
        perf_tracker.track_phase("File Processing")
    
    base_name = os.path.splitext(input_file)[0]
    output_file = f"{base_name}_optimized_bw.pdf"
    
    success, message = compress_single_pdf(
        input_file, output_file, quality_mode, 
        progress_callback, perf_tracker
    )
    
    if success:
        results = {
            'total_files': 1,
            'successful_compressions': 1,
            'failed_files': [],
            'total_original_size': os.path.getsize(input_file),
            'total_compressed_size': os.path.getsize(output_file),
            'output_file': output_file
        }
        return True, message, results
    else:
        results = {
            'total_files': 1,
            'successful_compressions': 0,
            'failed_files': [(os.path.basename(input_file), message)],
            'total_original_size': 0,
            'total_compressed_size': 0,
            'output_file': None
        }
        return False, message, results