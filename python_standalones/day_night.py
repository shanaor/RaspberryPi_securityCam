from python_standalones.automatic_camera_functions import get_frame_safe
from python_standalones.logger import log_event

import cv2
import numpy as np
import os
import time

# Threshold for night vision activation
BRIGHTNESS_THRESHOLD = 50  # Adjust based on testing
LOG_FILE = "/cameralog/camera_brightness_log.txt"  # File to store brightness log for debuging purposes
last_date = time.strftime('%Y-%m-%d')  # Store the current date

def get_brightness(frame):
    """Calculate the average brightness of a frame."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return np.mean(gray)

def get_current_mode():
    """Check the current mode from config.txt."""
    try:
        with open("/boot/config.txt", "r") as file:
            for line in file:
                if "disable_camera_led=1" in line:
                    return "night"
        return "normal"
    except Exception as e:
        log_event("critical", f"get_current_mode function error at day_night.py: {e}")
        return None
    
def update_config(new_mode):
    """Update the Raspberry Pi config file to switch modes."""
    config_path = "/boot/config.txt"

    try:
        # Read and modify config
        with open(config_path, "r") as file:
            lines = file.readlines()
        with open(config_path, "w") as file:
            for line in lines:
                if "disable_camera_led=" in line:
                    continue  # Remove existing setting
                file.write(line)
            if new_mode == "night":
                file.write("disable_camera_led=1\n")

        # Reboot after scheduled interval
        log_event("warning", f"Switching to {new_mode} mode. Restarting system in 5 minutes...")
        os.system("sleep 300 && sudo reboot &")  # Delay reboot by 5 minutes
    except Exception as e:
        log_event("critical", f"update_config function error at day_night.py: {e}")

def write_log(brightness,current_mode):
    global last_date
    try:
        current_date = time.strftime('%Y-%m-%d')  # Get today's date

        # If the day has changed, reset the log file (overwrite)
        if current_date != last_date:
            last_date = current_date  # Update the day counter to hold previous day date
            with open(LOG_FILE, "w") as log:  # "w" clears the file
                log.write(f"=== Log for {current_date} ===\n")  # Add a header

        # Append new log entry
        with open(LOG_FILE, "a") as log:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            log.write(f"{timestamp} - Brightness: {brightness} - Camera Mode: {current_mode}\n")
    except Exception as e:
            log_event("critical", f"write_log function error at day_night.py: {e}")

def monitor_brightness():
    """Continuously monitor brightness and switch modes when needed."""
    while True:
        try:
            low_brightness_count = 0
            high_brightness_count = 0
            checks = 10  # Checks 10 times within the interval (once per minute)

            for _ in range(checks):
                frame_local,ret = get_frame_safe()
                if not ret:
                    print("Failed to capture image")
                    write_log(None,None)
                    time.sleep(60)  # Waits 1 minute before retrying
                    continue

                brightness = get_brightness(frame_local)
                current_mode = get_current_mode()

                write_log(brightness,current_mode)

                if brightness < BRIGHTNESS_THRESHOLD:
                    low_brightness_count += 1
                else:
                    high_brightness_count += 1

                time.sleep(60)  # Waits 1 minute between checks

            # Only switchs if the brightness was consistently low/high for most checks
            if low_brightness_count >= 7 and current_mode == "normal":
                update_config("night")
            elif high_brightness_count >= 7 and current_mode == "night":
                update_config("normal")
        except Exception as e:
            log_event("critical", f"monitor_brightness function error at day_night.py: {e}")
            time.sleep(1)
            continue