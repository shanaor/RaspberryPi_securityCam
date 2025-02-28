from python_standalones.logger import log_event
from python_standalones.automatic_camera_functions import camera,recognize_face,camera_feed_function
from login import router_login_and_generate_token as login_and_generate_token
from livefeeds import(router_livefeed as live_feed_router,
                        router_register_livefeed as register_livefeed_router)
from users_and_logs_operations import ( router_register_user as register_user_router,
                                        router_delete_user as delete_user_router,
                                        router_deactivate_user as deactivate_user_router,
                                        router_activate_user as activate_user_router,
                                        router_user_list as user_list_router,
                                        router_get_event_logs as get_event_logs_router)
from video_operations import (  router_videos_list as video_list_router
                                ,router_video_download as video_download_router
                                ,router_delete_video as video_delete_router)
from register_face import (router_register_face as register_face_router,
                            router_delete_face as delete_face_router,
                            router_faces_list as faces_list_router)

from DB.users_logs_DB import initialize_user_and_logs_database
from DB.face_DB import initialize_face_db

from fastapi import FastAPI

import os
import time
import atexit
import uvicorn
import threading

app = FastAPI()

def cleanup(): #Ensure camera resources are released at exit
    """Release camera resources before exiting."""
    if camera.isOpened():
        camera.release()
        log_event("warning", "Camera resources released using atexit at main.py.")

retry_camera = 0
retry_recognition = 0

# Start camera thread with retry logic
while retry_camera < 5:
    try:
        camera_thread = threading.Thread(target=camera_feed_function, daemon=True)  # Recreate the thread
        camera_thread.start()
        log_event("info", "Camera feed thread started.")
        break  # Exit loop if successful
    except Exception as e:
        log_event("critical", f"Failed to start camera thread (Attempt {retry_camera + 1}/5): {e}")
        retry_camera += 1
        time.sleep(5)
if retry_camera == 5:
    log_event("critical", "Camera feed Thread start at main.py failed after 5 attempts. Exiting program.")
    exit(1)  # Prevents running without the camera
atexit.register(cleanup)  # Ensure cleanup runs on exit

# Start recognition thread with retry logic
while retry_recognition < 5:
    try:
        recognition_thread = threading.Thread(target=recognize_face, daemon=True)  # Recreate the thread
        recognition_thread.start()
        log_event("info", "Face recognition thread started.")
        break  # Exit loop if successful
    except Exception as e:
        log_event("critical", f"Failed to start face recognition thread (Attempt {retry_recognition + 1}/5): {e}")
        retry_recognition += 1
        time.sleep(5)
if retry_recognition == 5:
    log_event("critical", "Face recognition Thread at main.py start failed after 5 attempts. Exiting program.")
    exit(1)  # Prevents running without face recognition

app.include_router(login_and_generate_token)
# ---
app.include_router(live_feed_router)
# ---
app.include_router(video_list_router)
app.include_router(video_download_router)
app.include_router(video_delete_router)
# ---
app.include_router(register_livefeed_router)
app.include_router(register_user_router)
app.include_router(delete_user_router)
app.include_router(deactivate_user_router)
app.include_router(activate_user_router)
app.include_router(user_list_router)
# ---
app.include_router(get_event_logs_router)
# ---
app.include_router(register_face_router)
app.include_router(delete_face_router)
app.include_router(faces_list_router)

if __name__ == "__main__":
    startup_retry = 0
    while startup_retry < 5:
        try:
            # Ensure necessary directories exist
            os.makedirs("recordings", exist_ok=True)
            os.makedirs("logs", exist_ok=True)
            # Initialize databases
            initialize_user_and_logs_database()
            initialize_face_db()
            log_event( "info","Database initialized if not exists.")
            # Start server
            uvicorn.run(app, host="0.0.0.0", port=8000)
            break # Exit loop if setup successful
        except Exception as e:
            startup_retry += 1
            log_event("critical", f"Failure at main.py startup logic (Attempt {startup_retry}/5): {e}")
            time.sleep(5)  # Prevent spamming retries

    if startup_retry == 5:
        log_event("critical", "Startup at main.py failed after 5 attempts. Exiting program.")
        exit(1)  # Stop execution if startup fails