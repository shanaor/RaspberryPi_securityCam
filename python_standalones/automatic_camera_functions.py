from config.config import SC_DB_PATH, USER_LOG_DB_PATH
from python_standalones.day_night import monitor_brightness
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
    try:
        with frame_lock:
            frame_copy = frame.copy() if frame is not None else None
            return frame_copy, ret
    except Exception as e:
        log_event("critical", f"get_frame_safe function error at automatic_camera_functions.py: {e}")

def compute_encoding_hash(encoding):
    """Generate a unique scalar value from the face encoding."""
    return float(np.prod(encoding))  # Multiply all elements together for fast lookup

def retrieve_candidates(encoding_hash, tolerance=0.001):
    """Retrieve face records from the database with a close encoding hash."""
    try:
        conn = sqlite3.connect(SC_DB_PATH)
        cursor = conn.cursor()
        query = "SELECT id, first_name, last_name, encoding FROM registered_faces WHERE ABS(encoding_hash - ?) < ?"
        cursor.execute(query, (encoding_hash, tolerance))
        candidates = cursor.fetchall()
        conn.close()
        return candidates
    except sqlite3.Error as e:
        log_event("critical", f"retrieve_candidates function error at automatic_camera_functions.py: {e}")

def start_recording(video_name, frame_width, frame_height):
    """Starts recording a video and saves it in the 'recordings' directory."""
    global out, recording, video_path
    try:
        if not recording:
            video_path = f"recordings/{video_name}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(video_path, fourcc, 20.0, (frame_width, frame_height))
            recording = True
            log_event("info", f"Recording started: {video_name}.mp4")
    except Exception as e:
        log_event("critical", f"start_recording function error at automatic_camera_functions.py: {e}")

def stop_recording():
    """Stops the recording and saves the video file."""
    global out, recording, video_path
    try:
        if recording:
            recording = False
            out.release()
            log_event("info", f"Recording saved: {video_path}")
    except Exception as e:
        log_event("critical", f"stop_recording function error at automatic_camera_functions.py: {e}")

def log_event(event_type: str, description: str):
    try:
        conn = sqlite3.connect(USER_LOG_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO event_logs (event_type, description) VALUES (?, ?)", (event_type, description))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        log_event("critical", f"log_event function error at automatic_camera_functions.py: {e}")

def camera_feed_function():
    """Read camera frames and store them in the global variable."""
    global frame,ret
    # start nightvision check thread
    threading.Thread(target=monitor_brightness, daemon=True).start()
    
    while True:
        try:
            with frame_lock:
                ret, frame = camera.read()
            if not ret:
                frame = None  # Indicate no frame available
                log_event("error", "Camera_feed_function area error:Camera disconnected, retrying...")
                time.sleep(1)  # Brief pause before retry
                continue
        except Exception as e:
            log_event("critical", f"Camera_feed_function error at automatic_camera_functions: {e}")
            with frame_lock:
                frame = None
            time.sleep(1)  # Retry after delay
            continue
        time.sleep(0.05)  # Throttle FPS for 20 frames per second
        
def recognize_face():
    """Continuously scan for faces and recognize them automatically (Automatic Daemon Thread)."""
    while True:
        try:
            # Convert frame to RGB for face recognition
            with frame_lock:
                frame_local_copy = frame.copy()
            if frame_local_copy is not None and ret:
                rgb_frame = cv2.cvtColor(frame_local_copy, cv2.COLOR_BGR2RGB)
                # Detect faces
                face_locations = face_recognition.face_locations(rgb_frame)
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

                recognized_name = "Unknown"
                recognized_id = set()
                people = set()
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
                    log_event("info", f"{people} with ID's {recognized_id} were recognized, recorded, and saved to file {video_name}")
                elif recording:
                    stop_recording()
                time.sleep(0.01) # slow down loop speed for CPU efficiency
            else:
                time.sleep(0.01)
                continue
        except Exception as e:
            log_event("critical", f"recognize_face function error at automatic_camera_functions.py: {e}")
            time.sleep(1)
            continue