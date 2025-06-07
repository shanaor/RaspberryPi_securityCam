from python_standalones.logger import log_event
from config.config import BYTES_IN_MB

import os

def get_directory_size(directory_path):
    """Calculates the total size of all files in a directory."""
    total_size = 0
    try:
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            if os.path.isfile(item_path):
                total_size += os.path.getsize(item_path)
    except FileNotFoundError:
        log_event("error", f"Directory not found for size calculation (day_night_folder_protection.py): {directory_path}") #return 0 on errors to not break the script, it would take alot of time to config.txt to cause strain on memory
        return 0
    except Exception as e:
        log_event("error", f"Error calculating directory size for {directory_path} (day_night_folder_protection.py): {e}", exc_info=True)
        return 0 
    return total_size
# -------
def cleanup_backup_directory(directory_path, max_size_bytes, target_size_bytes):
    """
    Cleans up the backup directory if its size exceeds max_size_bytes.
    Deletes oldest files until the directory size is at or below target_size_bytes.
    """
    try:
        if not os.path.isdir(directory_path):
            log_event("warning", f"Backup cleanup: Directory {directory_path} does not exist or is not a directory (day_night_folder_protection.py).")
            return

        current_size_bytes = get_directory_size(directory_path)
        log_event("info", f"Backup directory {directory_path} current size: {current_size_bytes / BYTES_IN_MB:.2f}MB. Max allowed: {max_size_bytes / BYTES_IN_MB:.2f}MB (day_night_folder_protection.py).")

        if current_size_bytes > max_size_bytes:
            log_event("warning", f"Backup directory {directory_path} size ({current_size_bytes / BYTES_IN_MB:.2f}MB) exceeds limit ({max_size_bytes / BYTES_IN_MB:.2f}MB). Starting cleanup to reach ~{target_size_bytes / BYTES_IN_MB:.2f}MB (day_night_folder_protection.py).")
            
            # Get all files, filter for .bak if necessary, or all files
            files = [os.path.join(directory_path, f) for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f)) and f.endswith(".bak")]
            
            # Sort files by modification time (oldest first)
            files.sort(key=lambda f: os.path.getmtime(f))
            
            files_deleted_count = 0
            for file_to_delete in files:
                if current_size_bytes <= target_size_bytes:
                    break # Target size reached
                
                try:
                    file_size = os.path.getsize(file_to_delete)
                    os.remove(file_to_delete)
                    current_size_bytes -= file_size
                    files_deleted_count += 1
                    log_event("info", f"Backup cleanup: Deleted old backup {os.path.basename(file_to_delete)} ({file_size / BYTES_IN_MB:.5f}MB). Current dir size: {current_size_bytes / BYTES_IN_MB:.2f}MB. (day_night_folder_protection.py)")
                except Exception as e_del:
                    log_event("error", f"Backup cleanup: Failed to delete {file_to_delete} (day_night_folder_protection.py): {e_del}", exc_info=True)
            
            log_event("info", f"Backup cleanup finished. Deleted {files_deleted_count} file(s). Final dir size: {current_size_bytes / BYTES_IN_MB:.2f}MB.")
        else:
            log_event("info", f"Backup directory {directory_path}, size: {current_size_bytes / BYTES_IN_MB:.2f}MB is within limits ({target_size_bytes / BYTES_IN_MB:.2f}MB). No cleanup needed. (if its 0 an error accured.) (day_night_folder_protection.py)")

    except Exception as e:
        log_event("error", f"Error during backup directory cleanup for {directory_path} (day_night_folder_protection.py): {e}", exc_info=True)