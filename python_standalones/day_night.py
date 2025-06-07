from config.config import CONFIGTXT, CONFIG_BACKUP_DIR , BRIGHTNESS_LOG_FILE , BRIGHTNESS_THRESHOLD, MAX_BACKUP_DIR_SIZE_MB, TARGET_BACKUP_DIR_SIZE_MB, BYTES_IN_MB
from python_standalones.automatic_camera_functions import get_frame_safe,Global_cam_var
from python_standalones.day_night_folder_protection import cleanup_backup_directory
from python_standalones.logger import log_event

import cv2
import numpy as np
import os
import time
import shutil
import datetime

last_known_log_file_date = None

try: #This is part of triple attempts to make sure that the directory is created due to dealing with the config file. so it is importent.
    os.makedirs(CONFIG_BACKUP_DIR, exist_ok=True)
except Exception:
    try:
        os.makedirs(CONFIG_BACKUP_DIR, exist_ok=True)
    except Exception as e: # More specific exception
        log_event("warning", f"Could not create backup directory {CONFIG_BACKUP_DIR} (may already exist or permission issue): {e}")
    
def get_brightness(frame):
    """Calculate the average brightness of a frame."""
    if frame is None or frame.size == 0:
        log_event("warning", "Invalid frame (None or empty) received in get_brightness function (day_night.py)")
        return None
    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return np.mean(gray)
    except cv2.error as e:
        log_event("critical", f"OpenCV error at get_brightness function (day_night.py): {e}", exc_info=True)
        return None

def get_current_mode():
    """Check the current mode from config.txt. which his path is in config.py saved to CONFIGTXT"""
    try:
        with open(CONFIGTXT, "r") as file:
            for line in file:
                if "disable_camera_led=1" in line:
                    return "night"
        return "normal"
    except FileNotFoundError as e:
        log_event("critical", f"Config file not found: {CONFIGTXT} at get_current_mode (day_night.py): {e}") #Return "unknown" to avoid breaking the script, allow the app continue, and signal error to the programmer
        return "unknown"
    except PermissionError as e:
        log_event("critical", f"Permission denied reading {CONFIGTXT} at get_current_mode (day_night.py): {e}")
        return "unknown"
    except Exception as e:
        log_event("critical", f"Unexpected error at get_current_mode function (day_night.py): {e}", exc_info=True)
        return "unknown"

    
def update_config(new_mode):
    """Update the Raspberry Pi config file to switch modes and schedule reboot.
    Attempts to backup config.txt first to CONFIG_BACKUP_DIR, then to its own directory on failure. Calls for cleanup of directory if too big."""
    
        # --- Cleanup backup directory before creating a new backup ---
    try:
        cleanup_backup_directory(CONFIG_BACKUP_DIR, MAX_BACKUP_DIR_SIZE_MB * BYTES_IN_MB, TARGET_BACKUP_DIR_SIZE_MB * BYTES_IN_MB)
    except Exception as e_cleanup:
        log_event("error", f"Error encountered during pre-backup cleanup: {e_cleanup}", exc_info=True)
    # --- End of cleanup ---
    
    backup_made_successfully = False
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    config_filename = os.path.basename(CONFIGTXT)
    backup_filename = f"{os.path.splitext(config_filename)[0]}_{timestamp}.bak"

    # Attempt 1: Backup to primary backup directory
    primary_backup_path = os.path.join(CONFIG_BACKUP_DIR, backup_filename)
    try:
        # Ensure primary backup directory exists
        if not os.path.exists(CONFIG_BACKUP_DIR):
            log_event("info", f"Primary backup directory {CONFIG_BACKUP_DIR} does not exist. Attempting to create it. (update_config in day_night.py)")
            os.makedirs(CONFIG_BACKUP_DIR, exist_ok=True)
        
        if os.path.isdir(CONFIG_BACKUP_DIR): # Check if it's a directory
            shutil.copy2(CONFIGTXT, primary_backup_path) # copy2 preserves more metadata
            log_event("info", f"Config backup created at {primary_backup_path} (update_config in day_night.py)")
            backup_made_successfully = True
        else:
            log_event("warning", f"Primary backup path {CONFIG_BACKUP_DIR} is not a directory. Cannot create backup here. (update_config in day_night.py)")

    except Exception as e1:
        log_event("error", f"Failed to create backup in primary directory {primary_backup_path}: {e1}. Trying fallback. (update_config in day_night.py)", exc_info=True)

    # Attempt 2: Fallback to backup in the same directory as CONFIGTXT
    if not backup_made_successfully:
        try:
            config_dir = os.path.dirname(CONFIGTXT)
            fallback_backup_path = os.path.join(config_dir, backup_filename)
            shutil.copy2(CONFIGTXT, fallback_backup_path)
            log_event("info", f"Config backup created at fallback location: {fallback_backup_path} (update_config in day_night.py)")
            backup_made_successfully = True # Set even if primary failed but this succeeded
        except Exception as e2:
            log_event("critical", f"Failed to create backup in fallback directory {os.path.dirname(CONFIGTXT)} as well: {e2}. Proceeding without backup. (update_config in day_night.py)", exc_info=True)

    if not backup_made_successfully:
        log_event("critical", f"CRITICAL: Could not create any backup for {CONFIGTXT}. Modifications will be made to the original directly. (update_config in day_night.py)")

    try:
        # Read and modify config
        with open(CONFIGTXT, "r") as file:
            lines = file.readlines()
        with open(CONFIGTXT, "w") as file:
            for line in lines:
                if "disable_camera_led=" in line:
                    continue  # Remove existing setting
                file.write(line)
            if new_mode == "night":
                file.write("disable_camera_led=1\n")

        # Reboot after scheduled interval
        log_event("warning", f"Switching to {new_mode} mode. System will restart in 2 minutes. (update_config in day_night.py)")
        os.system("sudo shutdown -r +2")  # Reboots in 2 minutes and sends SIGTERM to the systems
    except FileNotFoundError as e:
        log_event("critical", f"Config file not found: {CONFIGTXT} during modification in update_config (day_night.py): {e}")
    except PermissionError as e:
        log_event("critical", f"Permission denied reading\writing {CONFIGTXT} during modification in update_config (day_night.py): {e}")
    except Exception as e:
        log_event("critical", f"update_config function error during file modification (day_night.py): {e}", exc_info=True)

def write_log(brightness,current_mode):
    """Appends brightness and mode to a daily log file."""
    global last_known_log_file_date
    try:
        current_date_str = time.strftime('%Y-%m-%d')
        reset_file = False

        if not os.path.exists(BRIGHTNESS_LOG_FILE):
            reset_file = True
        elif current_date_str != last_known_log_file_date:
            # Date might have changed, or script just started (None). Checking file content date.
            try:
                with open(BRIGHTNESS_LOG_FILE, "r") as log_read:
                    first_line = log_read.readline()
                    if not first_line.startswith("=== Log for ") or not first_line.strip().endswith(current_date_str + " ==="):
                        # Header is missing, or old date
                        reset_file = True
            except Exception:
                # Problem reading, safer to reset
                reset_file = True
        
        if reset_file:
            with open(BRIGHTNESS_LOG_FILE, "w") as log:  # "w" clears the file
                log.write(f"=== Log for {current_date_str} ===\n")
            last_known_log_file_date = current_date_str # Updating module in-memory run understanding, when app restarts it would be None again 

        # Append new log entry
        with open(BRIGHTNESS_LOG_FILE, "a") as log:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            brightness_str = f"{brightness:.2f}" if brightness is not None else "N/A"
            mode_str = current_mode if current_mode is not None else "Unknown" # Defensive coding, mode always returns "unkown" on error but this is for edge unexpected cases
            log.write(f"{timestamp} - Brightness: {brightness_str} - Camera Mode: {mode_str}\n")
    except Exception as e:
            log_event("critical", f"write_log function error (day_night.py): {e}", exc_info=True)

def monitor_brightness():
    """Continuously monitor brightness and switch modes when needed.
    designed to have 10 sconds ( 10 checks * time.sleep() ) sessions in order to get accurate change of enviroment situation 
    If change is needed its's changing the time.sleep. the lower the sleep time the faster it would react to changing environment but the more CPU it would use.
    
    the 9 checks are to avoid false positives of unitentional enviroment light change.
    if the brightness is low for 9 checks it will switch to night mode, if its high for 9 checks it will switch to normal(day) mode."""
    checks = 10  # Checks 10 times within the interval
    
    while Global_cam_var.loop_flag:
        try:
            low_brightness_count = 0
            high_brightness_count = 0

            for _ in range(checks):
                frame_local = get_frame_safe()
                if frame_local is None:
                    log_event("error", "monitor_brightness function error (day_night.py) :No Frame data, retrying...")
                    write_log(None, get_current_mode())
                    time.sleep(1)  # Waits 1 seconds before retrying to have 10 seconds brightness check sessions
                    continue

                brightness = get_brightness(frame_local)
                current_mode = get_current_mode()
                write_log(brightness,current_mode)

                if brightness is None: # Failed to get brightness from frame
                    time.sleep(1)
                    continue
                
                if brightness < BRIGHTNESS_THRESHOLD:
                    low_brightness_count += 1
                else:
                    high_brightness_count += 1

                time.sleep(1)  # Waits 1 seconds before retrying to have 10 seconds brightness check sessions

            # Only switchs if the brightness was consistently low/high for most checks
            if low_brightness_count >= 9 and current_mode == "normal":
                log_event("info", f"Consistent low brightness ({brightness:.2f}) detected. Switching to night mode. (monitor_brightness in day_night.py)")
                update_config("night")
            elif high_brightness_count >= 9 and current_mode == "night":
                log_event("info", f"Consistent high brightness ({brightness:.2f}) detected. Switching to normal mode. (monitor_brightness in day_night.py)")
                update_config("normal")
        except Exception as e:
            log_event("critical", f"monitor_brightness function error (day_night.py): {e}", exc_info=True)
            time.sleep(5) # Giving some time to let the unexpected error to fix itself
            continue