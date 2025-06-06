from config.config import VIDEO_FOLDER, SD_CARD_MEMORY_LIMIT,FREE_PERCENTAGE_TRAGET

from python_standalones.logger import log_event

import cv2

import os
import shutil

# Global variables
# ----------------
class Global_Rec_variable:
    "Handles recording object (out), video name (video_path), recording flag (recording) and clean up flag (cleanup_flag)"
    out = None
    # ^^^ The cv2.VideoWriter object used to write video frames to a file.
    video_path = None
    # ^^^ The path that would be the currently recording video file.
    recording = False
    # ^^^ Boolean indicating whether the system is currently recording video.
    cleanup_flag = False
    # ^^^ flag to prevent conflict between recording file writing and the cleanup process incase they happen to handle the same file (would happen only with overloaded SDcard)

def check_disk_space(threshold_percent=SD_CARD_MEMORY_LIMIT):
    """Checks the disk space and deletes old recordings if the threshold is reached."""
    # global cleanup_flag
    try:
        total, used, free = shutil.disk_usage("/")  # Assuming root partition for SD card
        percent_used = (used / total) * 100
        log_event("info", f"Disk usage: {percent_used:.2f}% (Threshold: {threshold_percent}%).. (check_disk_space in recording_config.py)")
        log_event("info", f"Percent used: {percent_used:.2f}, total: {total/(1024**3):.2f}, used: {used/(1024**3):.2f}, free: {free/(1024**3):.2f} (check_disk_space in recording_config.py)")

        if percent_used >= threshold_percent:
            log_event("warning", f"Disk space nearing capacity ({percent_used:.2f}%). Initiating cleanup... (check_disk_space in recording_config.py)")
            Global_Rec_variable.cleanup_flag = True
            cleanup_recordings()
    except Exception as e:
        log_event("critical", f"Error checking disk space (check_disk_space in recording_config.py): {e}")
        raise

def cleanup_recordings(target_free_percent=FREE_PERCENTAGE_TRAGET):
    """Deletes the oldest video files in the recordings folder until the target free space is reached."""
    # global cleanup_flag
    try:
        video_files = [f for f in os.listdir(VIDEO_FOLDER) if f.endswith(".mp4")]
        if not video_files:
            log_event("info", "No video files found in the recordings directory. (cleanup_recordings in recording_config.py)")
            return

        # Sort files by creation time (oldest first)
        video_files.sort(key=lambda f: os.path.getmtime(os.path.join(VIDEO_FOLDER, f)))

        total, used, free = shutil.disk_usage("/")
        total_gb = total // (2**30)
        free_gb = free // (2**30)
        log_event("info", f"Total disk space: {total_gb} GB, Free space: {free_gb} GB. (cleanup_recordings in recording_config.py)")

        target_free_space = total * (target_free_percent / 100)

        total_space_freed = 0
        deleted_count = 0
        for filename in video_files:
            file_path = os.path.join(VIDEO_FOLDER, filename)
            try:
                total_space_freed += os.path.getsize(file_path) / (1024 ** 3) # Convert bytes to GB
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                os.remove(file_path)
                log_event("info", f"Deleted oldest recording: {filename}, memory size: {size_mb:.2f}MB. (cleanup_recordings in recording_config.py)")
                deleted_count += 1

                # Re-check free space after deletion
                total, used, free = shutil.disk_usage("/")
                if free >= target_free_space:
                    log_event("info", f"Reached target free space ({target_free_percent}%). Cleanup complete. Deleted {deleted_count} files. total size: {total_space_freed:.3f} GB (cleanup_recordings in recording_config.py)")
                    break
            except OSError as e:
                log_event("error", f"Failed to delete {filename} (cleanup_recordings in recording_config.py): {e}", exc_info=True)
                continue
            except FileNotFoundError as ffe:
                log_event("critical", f"Error cleaning up recordings (cleanup_recordings in recording_config.py): {ffe}", exc_info=True)
                continue
            except PermissionError as pe:
                log_event("critical", f"Permission Error cleaning up recordings (cleanup_recordings in recording_config.py): {pe}")
                raise
            except Exception as e:
                log_event("error", f"Error deleting file '{filename}' (cleanup_recordings in recording_config.py): {e}", exc_info=True)
                continue
        # Final check to see if we reached the target free space
        if free < target_free_space:
            log_event("warning", f"Could not reach target free space ({target_free_percent}%) after deleting {deleted_count} files. Consider increasing storage or reducing recording frequency/quality. (cleanup_recordings in recording_config.py)")
            log_event("info", f" free bytes left: {free} , traget free bytes: {target_free_space} (cleanup_recordings in recording_config.py)")
    except FileNotFoundError as ffe:
        log_event("critical", f"Error cleaning up recordings (cleanup_recordings in recording_config.py): {ffe}")
        raise
    except OSError as e:
        log_event("critical", f"Error cleaning up recordings (cleanup_recordings in recording_config.py): {e}")
        raise
    except PermissionError as pe:
        log_event("critical", f"Error cleaning up recordings (cleanup_recordings in recording_config.py): {pe}")
        raise
    except Exception as e:
        log_event("critical", f"Error cleaning up recordings (cleanup_recordings in recording_config.py): {e}")
        raise
    finally:
        Global_Rec_variable.cleanup_flag = False
        log_event("info", "Cleanup flag reset to False. (cleanup_recordings in recording_config.py)")
        
def start_recording(video_name: str, frame_width: int, frame_height: int, fps: float = 20.0):
    """Starts recording a video and saves it in the 'recordings' directory.
    Args:
        video_name (str): The base name for the video file (e.g., 'unknown_2023-10-01').
        frame_width (int): The width of the video frames in pixels.
        frame_height (int): The height of the video frames in pixels.
        fps (float, optional): Frames per second  for the video. Defaults to 20.0.
    Raises:
        ValueError: If frame_width or frame_height are not positive integers.
        Exception: For other errors, logged as critical.
    """
    # global out, recording, video_path
    try:
        if not Global_Rec_variable.recording:
            # Validate frame dimensions
            if frame_width <= 0 or frame_height <= 0:
                raise ValueError("Frame dimensions must be positive integers in start_recording function (start_recording in recording_config.py).")
            
            # Ensure the recordings directory exists
            try:
                if not os.path.exists(VIDEO_FOLDER):
                    log_event("info", f"Recordings directory '{VIDEO_FOLDER}' does not exist, too late creation. defencive code. (start_recording in recording_config.py)")
                    os.makedirs(f"{VIDEO_FOLDER}", exist_ok=True)
            except OSError as e:
                if not os.path.exists(VIDEO_FOLDER):
                    log_event("critical", f"Failed to create recordings directory '{VIDEO_FOLDER}'. if it reached here, its failure of 3rd defensive creation code. (start_recording in recording_config.py): {e}")
                    raise
            
            # Set up the video file path and writer
            Global_Rec_variable.video_path = f"{VIDEO_FOLDER}/{video_name}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            Global_Rec_variable.out = cv2.VideoWriter(Global_Rec_variable.video_path, fourcc, fps, (frame_width, frame_height))
            Global_Rec_variable.recording = True
            log_event("info", f"Recording started: {video_name}.mp4 with FPS: {fps}, (start_recording in recording_config.py)")
    except cv2.error as e:
        log_event("critical", f"OpenCV error in start_recording function (start_recording in recording_config.py): {e}")
        raise
    except Exception as e:
        log_event("critical", f"start_recording function error (start_recording in recording_config.py): {e}")
        raise  # Re-raise the exception after logging for caller awareness

def stop_recording():
    """Stops the recording and saves the video file."""
    # global out, recording, video_path
    try:
        if Global_Rec_variable.recording and Global_Rec_variable.out is not None:
            if Global_Rec_variable.out.isOpened():
                Global_Rec_variable.out.release()
            log_event("info", f"Recording saved: {Global_Rec_variable.video_path}")
            video = cv2.VideoCapture(f"{Global_Rec_variable.video_path}")
            fps = video.get(cv2.CAP_PROP_FPS)
            frame_count = video.get(cv2.CAP_PROP_FRAME_COUNT)
            duration = (frame_count / fps) if fps > 0 else 0 # Avoid division by zero
            log_event("info", f"Video FPS: {fps}, Frame Count: {frame_count}, Duration: {duration} seconds (stop_recording in recording_config.py).")
        else:
            log_event("warning", "Stop_recording called but no active recording or writer (stop_recording in recording_config.py).")
    except Exception as e:
        log_event("critical", f"stop_recording function error (stop_recording in recording_config.py): {e}")
        raise
    finally:
        Global_Rec_variable.recording = False
        Global_Rec_variable.out = None
        Global_Rec_variable.video_path = None  