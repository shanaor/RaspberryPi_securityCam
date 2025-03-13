import os
from config.config import SC_DB_PATH, USER_LOG_DB_PATH,VIDEO_FOLDER
from python_standalones.logger import log_event

import time
import threading
import datetime
import cv2
import numpy as np
import sqlite3
import face_recognition
# ------------------------------------------------------------
# ------------------------------------------------------------
""""""""""""""""""""""""""""""""""""
""""""""" AUTOMATIC MODULE """""""""
""""""""""""""""""""""""""""""""""""

recording = False
out = None
video_path = None
frame = None
ret = None
camera = cv2.VideoCapture(0)
frame_lock = threading.Lock()

def get_frame_safe(): #async executor
    "Returns a thread-safe copy of the current frame and its status for async functions to prevent crash."
    try:
        with frame_lock:
            frame_copy = frame.copy() if frame is not None and ret else None
        return frame_copy, ret
    except Exception as e:
        log_event("critical", f"get_frame_safe function error at automatic_camera_functions.py: {e}")
        return None, False

def compute_encoding_hash(encoding):
    """Generate a scalar value from a face encoding for fast database lookup."""
    product = np.prod(encoding)
    return float(min(max(product, -1e308), 1e308))  # Multiply all elements together for fast lookup

def retrieve_candidates(encoding_hash: float, tolerance: float = 0.001) -> list:
    """Retrieve candidate face records from the database where the encoding_hash is within the specified tolerance for fast pre-filtering in face recognition."""
    try:
        with sqlite3.connect(SC_DB_PATH) as conn:
            cursor = conn.cursor()
            query = "SELECT id, first_name, last_name, encoding FROM registered_faces WHERE ABS(encoding_hash - ?) < ?"
            cursor.execute(query, (encoding_hash, tolerance))
            candidates = cursor.fetchall()
        return candidates
    except sqlite3.Error as e:
        log_event("critical", f"retrieve_candidates function error at automatic_camera_functions.py: {e}")
        return []

def start_recording(video_name: str, frame_width: int, frame_height: int, fps: float = 20.0):
    """Starts recording a video and saves it in the 'recordings' directory.
    Args:
        video_name (str): The base name for the video file (e.g., 'unknown_2023-10-01').
        frame_width (int): The width of the video frames in pixels.
        frame_height (int): The height of the video frames in pixels.
        fps (float, optional): Frames per second for the video. Defaults to 20.0.
    Raises:
        ValueError: If frame_width or frame_height are not positive integers.
        Exception: For other errors, logged as critical.
    """
    global out, recording, video_path
    try:
        if not recording:
            # Validate frame dimensions
            if frame_width <= 0 or frame_height <= 0:
                raise ValueError("Frame dimensions must be positive integers.")
            
            # Ensure the recordings directory exists
            os.makedirs(f"{VIDEO_FOLDER}", exist_ok=True)
            
            # Set up the video file path and writer
            video_path = f"{VIDEO_FOLDER}/{video_name}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(video_path, fourcc, fps, (frame_width, frame_height))
            recording = True
            log_event("info", f"Recording started: {video_name}.mp4")
    except Exception as e:
        log_event("critical", f"start_recording function error at automatic_camera_functions.py: {e}")
        raise  # Re-raise the exception after logging for caller awareness

def stop_recording():
    """Stops the recording and saves the video file."""
    global out, recording, video_path
    try:
        if recording and out is not None:
            log_event("info", f"Recording saved: {video_path}")
            out.release()
        else:
            log_event("warning", "Stop_recording called but no active recording or writer.")
    except Exception as e:
        log_event("critical", f"stop_recording function error at automatic_camera_functions.py: {e}")
    finally:
        recording = False
        out = None
        video_path = None  

def log_event_db(event_type: str, description: str):
    """Log recording events to the database for admin review (e.g., when a video is saved)."""
    try:
        with sqlite3.connect(USER_LOG_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO event_logs (event_type, description) VALUES (?, ?)", (event_type, description))
            conn.commit()
    except sqlite3.Error as e:
        log_event("critical", f"log_event_db function error at automatic_camera_functions.py: {e}")

def camera_feed_function():
    """Read camera frames and store them in the global variable (Automatic Daemon Thread started at main.py)."""
    global frame,ret,camera
    retry_delay = 1  # Initial delay in seconds
    max_delay = 30  # Maximum delay seconds
    while True:
        try:
            with frame_lock:
                ret,frame = camera.read()
            if not ret:
                frame = None  # Indicate no frame available
                log_event("error", "Camera_feed_function error at automatic_camera_functions.py: Camera disconnected, retrying...")
                camera.release()
                camera = cv2.VideoCapture(0)  # Reinitialize camera
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_delay)  # Exponential backoff
                continue
            else:
                retry_delay = 1  # Reset delay on success
                time.sleep(0.05)  # ~20 FPS
        except Exception as e:
            log_event("critical", f"Camera_feed_function error at automatic_camera_functions.py: Unexpected error - {e}")
            with frame_lock:
                frame = None
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, max_delay)  # Retry after delay
            continue
        
def recognize_face():
    """Continuously scan for faces and recognize them automatically (Automatic Daemon Thread started at main.py)."""
    recognized_name = "Unknown"
    recognized_id = set()
    people = set()
    video_name = None # if by fringe chance log_event shows video_name as None, it indicates error in the code. should be "unknown+date" or "name+date"
    while True:
        try:
            with frame_lock:
                frame_local_copy = frame.copy() if frame is not None and ret else None
            if frame_local_copy is not None:
                rgb_frame = cv2.cvtColor(frame_local_copy, cv2.COLOR_BGR2RGB) # Convert frame to RGB for face recognition
                # Detect faces
                face_locations = face_recognition.face_locations(rgb_frame)
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

                if face_encodings:
                    for face_encoding in face_encodings:
                        input_hash = compute_encoding_hash(face_encoding)
                        candidates = retrieve_candidates(input_hash)

                        if candidates:
                            for person_id, first_name, last_name, stored_encoding_blob in candidates:
                                stored_encoding = np.frombuffer(stored_encoding_blob, dtype=np.float64)
                                match = face_recognition.compare_faces([stored_encoding], face_encoding)[0]
                                if match:
                                    recognized_name = f"{first_name}_{last_name}"
                                    recognized_id.add(person_id)
                                    people.add(recognized_name)
                                else:
                                    recognized_name = "Unknown"
                                    people.add(recognized_name)
                                if not recording:
                                    timestamp = datetime.datetime.now().strftime("%d_%m_%Y_%H_%M")
                                    video_name = f"{recognized_name}_{timestamp}"
                                    frame_width = int(camera.get(3))
                                    frame_height = int(camera.get(4))
                                    start_recording(video_name, frame_width, frame_height)
                elif recording:
                    stop_recording()
                    log_msg = f"{people} with ID's {recognized_id} were recognized, recorded, and saved to file {video_name}"
                    log_event("info", log_msg) 
                    log_event_db("Face detected", log_msg)
                    recognized_name = "Unknown"  # Reset after recording ends
                    recognized_id.clear()
                    people.clear()
                time.sleep(0.05)  # ~20 FPS, synced with camera_feed
            else:
                time.sleep(0.05)
                continue
        except Exception as e:
            log_event("critical", f"recognize_face function error at automatic_camera_functions.py: {e}")
            time.sleep(1)
            continue