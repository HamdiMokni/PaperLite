import subprocess
import os
import time
import shutil
import logging
from file_utils import calculate_timeout, safe_remove_file, create_temp_file

logger = logging.getLogger(__name__)

def compress_single_pdf(input_file, output_file, quality_mode="balanced", progress_callback=None, perf_tracker=None):
    """Compress a single PDF file with improved error handling and adaptive timeout"""
    file_start_time = time.time()
    
    if not os.path.exists(input_file):
        error_msg = f"❌ File not found: '{input_file}'"
        logger.error(error_msg)
        return False, error_msg

    # Calculate appropriate timeout based on file size
    timeout = calculate_timeout(input_file)

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
        
        # Run with adaptive timeout
        logger.info(f"🔄 Starting Ghostscript with {timeout/60:.1f} minute timeout...")
        
        # Create process with real-time monitoring
        process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            universal_newlines=True
        )
        
        # Monitor process with periodic updates
        poll_interval = 10  # Check every 10 seconds
        elapsed_time = 0
        
        while process.poll() is None:
            time.sleep(poll_interval)
            elapsed_time += poll_interval
            
            # Update progress if callback provided
            if progress_callback:
                progress_callback(f"⏳ Processing... {elapsed_time//60:.0f}:{elapsed_time%60:02.0f} elapsed")
            
            logger.info(f"⏳ Ghostscript still running... {elapsed_time//60:.0f}:{elapsed_time%60:02.0f} elapsed")
            
            # Check timeout
            if elapsed_time >= timeout:
                logger.warning(f"⏰ Timeout reached ({timeout/60:.1f} minutes), terminating process...")
                process.terminate()
                try:
                    process.wait(timeout=10)  # Wait 10 seconds for graceful termination
                except subprocess.TimeoutExpired:
                    logger.error("🔴 Force killing Ghostscript process")
                    process.kill()
                    process.wait()
                
                error_msg = f"❌ Ghostscript timeout ({timeout/60:.1f} minutes) for file: {input_file}"
                logger.error(error_msg)
                safe_remove_file(temp_output_file)
                if perf_tracker:
                    perf_tracker.track_file(input_file, file_start_time, success=False)
                return False, error_msg
        
        # Get final result
        stdout, stderr = process.communicate()
        gs_duration = time.time() - gs_start_time
        
        if process.returncode != 0:
            error_msg = f"❌ Ghostscript error (code {process.returncode}): {stderr}"
            logger.error(error_msg)
            logger.error(f"Ghostscript stdout: {stdout}")
            
            # Clean up temp file
            safe_remove_file(temp_output_file)
            if perf_tracker:
                perf_tracker.track_file(input_file, file_start_time, success=False)
            return False, error_msg
        
        # Check if output file was created and is valid
        if not os.path.exists(temp_output_file) or os.path.getsize(temp_output_file) == 0:
            error_msg = f"❌ Output file not created or empty: {temp_output_file}"
            logger.error(error_msg)
            safe_remove_file(temp_output_file)
            if perf_tracker:
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
            if perf_tracker:
                perf_tracker.track_file(input_file, file_start_time, success=False)
            return False, error_msg
        
        # Track successful file processing
        if perf_tracker:
            perf_tracker.track_file(input_file, file_start_time, success=True)
        
        # Log detailed timing info
        file_duration = time.time() - file_start_time
        logger.info(f"✅ {os.path.basename(input_file)}: {file_duration:.2f}s (GS: {gs_duration:.2f}s)")
        
        return True, "✅ Compression successful"
        
    except Exception as e:
        error_msg = f"❌ Unexpected error processing {input_file}: {e}"
        logger.error(error_msg)
        if temp_output_file:
            safe_remove_file(temp_output_file)
        if perf_tracker:
            perf_tracker.track_file(input_file, file_start_time, success=False)
        return False, error_msg

def check_ghostscript():
    """Check if Ghostscript is available"""
    try:
        result = subprocess.run(["gswin64c", "-version"], capture_output=True, check=True)
        gs_version = result.stdout.decode().strip().split('\n')[0]
        logger.info(f"✅ Ghostscript found: {gs_version}")
        return True, gs_version
    except (subprocess.CalledProcessError, FileNotFoundError):
        error_msg = "❌ Ghostscript not found. Please install Ghostscript first."
        logger.error(error_msg)
        return False, error_msg