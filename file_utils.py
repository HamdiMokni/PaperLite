import os
import time
import tempfile
import logging

logger = logging.getLogger(__name__)

def get_file_size(file_path):
    """Get file size in MB"""
    try:
        return os.path.getsize(file_path) / (1024 * 1024)
    except:
        return 0

def calculate_timeout(file_path):
    """Calculate appropriate timeout based on file size"""
    file_size_mb = get_file_size(file_path)
    
    # Base timeout: 2 minutes
    base_timeout = 120
    
    # Additional time based on file size
    if file_size_mb < 1:
        additional_time = 60  # 1 minute for small files
    elif file_size_mb < 10:
        additional_time = 180  # 3 minutes for medium files
    elif file_size_mb < 50:
        additional_time = 600  # 10 minutes for large files
    else:
        additional_time = 1200  # 20 minutes for very large files
    
    total_timeout = base_timeout + additional_time
    
    logger.info(f"📏 File size: {file_size_mb:.2f}MB, Timeout: {total_timeout/60:.1f} minutes")
    return total_timeout

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