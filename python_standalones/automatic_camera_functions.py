from python_standalones.recording_config import start_recording,stop_recording,check_disk_space,Global_Rec_variable
from config.config import SC_DB_PATH, USER_LOG_DB_PATH,FRAME_TIME_INTERVAL,SD_CARD_MEMORY_LIMIT,FRAME_LIMITER
from python_standalones.logger import log_event

import cv2
import numpy as np
import sqlite3
import face_recognition
from picamera2 import Picamera2

import shutil
import threading
import datetime
import time
import asyncio
# ------------------------------------------------------------
# ------------------------------------------------------------
""""""""""""""""""""""""""""""""""""
""""""""" AUTOMATIC MODULE """""""""
""""""""""""""""""""""""""""""""""""
# Global variables
# ----------------
class Global_cam_var:
    """Manages thread function loop state (loop flag) and frame access lock to prevent datarace."""
    frame = None
    # ^^^ most recent frame captured from camera. Accessed by camera_feed_function, get_frame_safe and recognize_face function.
    loop_flag = True
    # ^^^ Flag to control the loop of thread functions and day_night.py loop. Set to False on exit by Cleanup for gracious stop.
    frame_lock = threading.Lock()
    # ^^^ Lock to protect access to the 'frame' variable, ensuring no conflict for all functions using "frame".
picam2 = Picamera2()
# ^^^ Picamera2 instance for capturing images. Initialized in camera_feed_function.

# ---------------------------------------------------------------------------------------------------------------------------------------------
#  --------------------------------------------------------------------------------------------------------------------------------------------
async def cleanup(): #Ensure camera resources are released at exit from shutdown in main.py without blocking the uvicorn server shutdown process
    """Release camera resources before exiting."""
    global picam2
    try:
        if  picam2 is not None and hasattr(picam2, 'is_open') and picam2.is_open:
            Global_cam_var.loop_flag = False
            await asyncio.sleep(0.1) #Give the threads alittle time to shutdown to prevent a hiccup
            log_event("info", "Stoping camera (cleanup function automatic_camera_functions.py).")
            await asyncio.to_thread(picam2.stop)
            log_event("info", "Camera stopped, closing (cleanup function automatic_camera_functions.py).")
            await asyncio.to_thread(picam2.close)
            log_event("info", "Camera resources released and thread loops stopped using cleanup function (automatic_camera_functions.py).")
        else:
            is_open_status = 'Attribute missing or object is None' # Default explanation
            picam_exists = picam2 is not None
            if picam_exists and hasattr(picam2, 'is_open'):
                is_open_status = picam2.is_open # Get status if attribue exists
            log_event("warning", f"Cleanup called, but no action taken. Picam object exists: {picam_exists}, Is open status: {is_open_status}, Loop flag: {Global_cam_var.loop_flag}")
            print(f"Cleanup: No action taken. Picam exists: {picam_exists}, Open Status: {is_open_status}") # print fallback
    except Exception as e:
        log_event("critical", f"Error during cleanup function using FastAPI shutdown event in main.py (automatic_camera_functions.py): Picam resource:{picam2}, flag: {Global_cam_var.loop_flag}. Error detail: {e}")
        print(f"CRITICAL: Error during cleanup: {e}") #emergency logging incase of failure in shutdown
        
def compute_encoding_hash(encoding):
    """Generate a scalar value from a face encoding for fast database lookup."""
    try:
        return float(min(max(np.prod(encoding), -1e308), 1e308))  # Multiply all elements together for fast lookup, and clamp to avoid overflow
    except OverflowError:
        log_event("critical", "Overflow error in compute_encoding_hash function (automatic_camera_functions.py)")
        return None
    except Exception as e:
        log_event("critical", f"compute_encoding_hash function error (automatic_camera_functions.py): {e}")
        return None

def get_frame_safe(): #async executor
    "Returns a thread-safe copy of the current frame and its status for async functions to prevent crash."
    try:
        with Global_cam_var.frame_lock:
            return Global_cam_var.frame.copy() if Global_cam_var.frame is not None else None
    except cv2.error as e:
        log_event("critical", f"OpenCV error in get_frame_safe function (automatic_camera_functions.py): {e}")
        return None
    except Exception as e:
        log_event("critical", f"get_frame_safe function error (automatic_camera_functions.py): {e}")
        return None
    finally:
        if Global_cam_var.frame is None:
            log_event("debug", "No frame available in get_frame_safe function (automatic_camera_functions.py).")

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
        log_event("critical", f"retrieve_candidates function error (automatic_camera_functions.py): {e}")
        return []

def log_event_db(event_type: str, description: str):
    """Log recording events to the database for admin review (e.g., when a video is saved)."""
    try:
        with sqlite3.connect(USER_LOG_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO event_logs (event_type, description) VALUES (?, ?)", (event_type, description))
            conn.commit()
        log_event("info", f"Event logged to database: {event_type} - {description} (log_event_db function at automatic_camera_functions.py)")
    except sqlite3.Error as e:
        log_event("critical", f"log_event_db function error (automatic_camera_functions.py): {e}")

def camera_feed_function():
    """Read camera frames and store them in the global variable (Automatic Daemon Thread started at main.py)."""
    global picam2
    retry_delay = 1  # Initial delay in seconds
    max_delay = 30  # Maximum delay seconds
    
    try:
        # Initializing picamera2 globally
        picam2.preview_configuration.main.size = (640, 480)  # Setting resolution
        picam2.preview_configuration.main.format = "BGR888"  # BGR format for OpenCV compatibility
        picam2.configure("preview") # changing the deafult config
        picam2.start()
        log_event("info", "Camera initialized successfully (camera_feed_function at automatic_camera_functions.py).")
    except Exception as e:
        log_event("critical", f"Failed to configure or start camera (camera_feed_function at automatic_camera_functions.py): {e}") 
        
    while Global_cam_var.loop_flag:
        try:
            # Capture frame as a NumPy array
            with Global_cam_var.frame_lock:
                Global_cam_var.frame = picam2.capture_array()
            time.sleep(FRAME_TIME_INTERVAL)  # ~20 FPS
            retry_delay = 1  # Reset delay on success
            continue
        except Exception as e:
            with Global_cam_var.frame_lock:
                Global_cam_var.frame = None  # Indicate no frame available
            log_event("critical", f"Camera_feed_function error (automatic_camera_functions.py): Camera disconnected, retrying...: {e}")
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, max_delay)  # Exponential backoff
            picam2.stop()
            picam2.close()
            try:
                picam2 = Picamera2()
                picam2.preview_configuration.main.size = (640, 480)  # Set resolution
                picam2.preview_configuration.main.format = "BGR888"  # Set format compatible with OpenCV
                picam2.configure("preview")
                picam2.start()  # Reinitialize camera
                log_event("info", "Camera reinitialized successfully (camera_feed_function at automatic_camera_functions.py).")
                continue
            except Exception as restart_error:
                log_event("critical", f"Failed to reinitialize camera (camera_feed_function at automatic_camera_functions.py): {restart_error}")
                continue
        
def recognize_face():
    """Continuously scan for faces and recognize them automatically (Automatic Daemon Thread started at main.py)."""
    global picam2
    recognized_name = "Unknown"
    recognized_id = set()
    people = set()
    video_name = None # if by fringe chance log_event shows video_name as None, it indicates error in the code. should be "unknown+date" or "name+date"
    # frame_counter = 0 # to control frame flow incase CPU cant handle 20fps on face recognition
    while Global_cam_var.loop_flag:
        start_time = time.time()
        try:
            with Global_cam_var.frame_lock:
                frame_local_copy = Global_cam_var.frame.copy() if Global_cam_var.frame is not None else None
            if frame_local_copy is None:
                time.sleep(max(FRAME_TIME_INTERVAL - (time.time() - start_time), 0))
                continue
            # Write frame to video if recording
            if Global_Rec_variable.recording and not Global_Rec_variable.cleanup_flag:
                Global_Rec_variable.out.write(frame_local_copy)
                total, used, free = shutil.disk_usage("/")  # Assuming root partition for SD card
                percent_used = (used / total) * 100 # check SD card percentage used
                if percent_used >= SD_CARD_MEMORY_LIMIT:
                    stop_recording()
                    check_disk_space()
            #  !!!! --- INCASE FRAME CONTROL IS NEEDED --- !!!!
            # frame_counter += 1
            # if frame_counter % FRAME_LIMITER == 0:
            #     time.sleep(max(FRAME_TIME_INTERVAL - (time.time() - start_time), 0))  # ~20 FPS, synced with camera_feed
            #     frame_counter = 0
            #     continue
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
                    elif not candidates:
                        recognized_name = "Unknown"
                        people.add(recognized_name)
                    if not Global_Rec_variable.recording:
                        timestamp = datetime.datetime.now().strftime("%d_%m_%Y_%H_%M")
                        video_name = f"{recognized_name}_{timestamp}"
                        frame_width = frame_local_copy.shape[1]
                        frame_height = frame_local_copy.shape[0]
                        if not Global_Rec_variable.cleanup_flag:
                            start_recording(video_name, frame_width, frame_height)
            elif Global_Rec_variable.recording:
                stop_recording()
                face_id = recognized_id if recognized_id else 'unknown'
                log_msg = f"{people} with ID's {face_id} were recognized, recorded, and saved to file {video_name}"
                log_event("info", log_msg) 
                log_event_db("Face detected", log_msg)
                recognized_name = "Unknown"  # Reset after recording ends
                recognized_id.clear()
                people.clear()
            time.sleep(max(FRAME_TIME_INTERVAL - (time.time() - start_time), 0))  # ~20 FPS, synced with camera_feed
        except cv2.error as e:
            log_event("critical", f"OpenCV error in recognize_face (automatic_camera_functions.py): {e}")
            time.sleep(1)
            continue
        except Exception as e:
            log_event("critical", f"recognize_face function error (automatic_camera_functions.py): {e}")
            time.sleep(1)
            continue
        
# --------IMPROVMENT OPTIONS FOR LATER CASE -----------
# checking if a frame freezed: 
# saving former frame and compare it to the new request frame to see if its the exact 1