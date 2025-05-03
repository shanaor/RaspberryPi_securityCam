from config.config import CONFIGTXT, CONFIG_BACKUP_DIR , BRIGHTNESS_LOG_FILE
from python_standalones.automatic_camera_functions import get_frame_safe,Global_cam_var
from python_standalones.logger import log_event

import cv2
import numpy as np
import os
import time
import shutil
import datetime

# Threshold for night vision activation
BRIGHTNESS_THRESHOLD = 50  # Adjust based on testing
last_date = time.strftime('%Y-%m-%d')  # Store the current date

try:
    os.makedirs(CONFIG_BACKUP_DIR, exist_ok=True)
except Exception:
    os.makedirs(CONFIG_BACKUP_DIR, exist_ok=True)
    
def get_brightness(frame):
    """Calculate the average brightness of a frame."""
    if frame is None or frame.size == 0:
        raise ValueError("Invalid frame received")
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return np.mean(gray)

def get_current_mode():
    """Check the current mode from config.txt. which his path is in config.py saved to CONFIGTXT"""
    try:
        with open(f"{CONFIGTXT}", "r") as file:
            for line in file:
                if "disable_camera_led=1" in line:
                    return "night"
        return "normal"
    except FileNotFoundError as e:
        log_event("critical", f"Config file not found: {CONFIGTXT} at get_current_mode (day_night.py): {e}")
        return None
    except PermissionError as e:
        log_event("critical", f"Permission denied reading {CONFIGTXT} at get_current_mode (day_night.py): {e}")
        return None
    except Exception as e:
        log_event("critical", f"Unexpected error at get_current_mode function (day_night.py): {e}")
        return None
    
def update_config(new_mode):
    """Update the Raspberry Pi config file to switch modes.
    CONFIGTXT is the config.txt path imported from config.py."""

    try:
        # Create a timestamped backup for config
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_path = f"{CONFIG_BACKUP_DIR}/config_{timestamp}.bak"
        shutil.copy(CONFIGTXT, backup_path)
        log_event("info", f"Config backup created at {backup_path} (day_night.py)")
        
        # Read and modify config
        with open(f"{CONFIGTXT}", "r") as file:
            lines = file.readlines()
        with open(f"{CONFIGTXT}", "w") as file:
            for line in lines:
                if "disable_camera_led=" in line:
                    continue  # Remove existing setting
                file.write(line)
            if new_mode == "night":
                file.write("disable_camera_led=1\n")

        # Reboot after scheduled interval
        log_event("warning", f"Function update_config in day_night.py activated. Switching to {new_mode} mode (day_night.py). Restarting system in 2 minutes...")
        os.system("sudo shutdown -r +2")  # Reboots in 2 minutes and sends SIGTERM to the systems
    except FileNotFoundError as e:
        log_event("critical", f"Config file not found: {CONFIGTXT} at function update_config (day_night.py): {e}")
    except PermissionError as e:
        log_event("critical", f"Permission denied reading\writing {CONFIGTXT} at function update_config (day_night.py): {e}")
    except Exception as e:
        log_event("critical", f"update_config function error (day_night.py): {e}")
        raise

def write_log(brightness,current_mode):
    global last_date
    try:
        current_date = time.strftime('%Y-%m-%d')  # Get today's date

        # If the day has changed, reset the log file (overwrite)
        if current_date != last_date:
            last_date = current_date  # Update the day counter to hold previous day date
            with open(BRIGHTNESS_LOG_FILE, "w") as log:  # "w" clears the file
                log.write(f"=== Log for {current_date} ===\n")  # Add a header

        # Append new log entry
        with open(BRIGHTNESS_LOG_FILE, "a") as log:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            log.write(f"{timestamp} - Brightness: {brightness} - Camera Mode: {current_mode}\n")
    except Exception as e:
            log_event("critical", f"write_log function error (day_night.py): {e}")
            raise

def monitor_brightness():
    """Continuously monitor brightness and switch modes when needed.
    designed to have 10 sconds ( 10 checks * time.sleep() ) sessions in order to get accurate change of enviroment situation 
    Change the time.sleep as need. the lower the sleep time the faster it would react to changing environment but the more CPU it would use.
    
    the 9 checks are to avoid false positives of unitentional enviroment light change.
    if the brightness is low for 9 checks it will switch to night mode, if its high for 9 checks it will switch to normal(day) mode."""
    
    while Global_cam_var.loop_flag:
        try:
            low_brightness_count = 0
            high_brightness_count = 0
            checks = 10  # Checks 10 times within the interval

            for _ in range(checks):
                frame_local = get_frame_safe()
                if frame_local is None:
                    log_event("error", "monitor_brightness function error (day_night.py) :Camera disconnected, retrying...")
                    write_log(None,None)
                    time.sleep(1)  # Waits 1 seconds before retrying to have 10 seconds brightness check sessions
                    continue

                brightness = get_brightness(frame_local)
                current_mode = get_current_mode()

                write_log(brightness,current_mode)

                if brightness < BRIGHTNESS_THRESHOLD:
                    low_brightness_count += 1
                else:
                    high_brightness_count += 1

                time.sleep(1)  # Waits 1 seconds before retrying to have 10 seconds brightness check sessions

            # Only switchs if the brightness was consistently low/high for most checks
            if low_brightness_count >= 9 and current_mode == "normal":
                update_config("night")
            elif high_brightness_count >= 9 and current_mode == "night":
                update_config("normal")
        except Exception as e:
            log_event("critical", f"monitor_brightness function error (day_night.py): {e}", exc_info=True)
            time.sleep(1)
            continue