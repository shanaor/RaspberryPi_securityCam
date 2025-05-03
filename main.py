
from python_standalones.day_night import monitor_brightness
from python_standalones.logger import log_event
from python_standalones.automatic_camera_functions import recognize_face,camera_feed_function, cleanup as cleanup_camera_resources
from config.config import VIDEO_FOLDER, LOG_DIR, SC_DB_PATH,USER_LOG_DB_PATH

from login import router_login_and_generate_token
from livefeeds import router_livefeed, router_register_livefeed
from users_and_logs_operations import ( router_register_user, router_delete_user,
                                        router_deactivate_user, router_activate_user,
                                        router_user_list, router_get_event_logs)
from video_operations import  router_videos_list ,router_video_download ,router_delete_video
from register_face import router_register_face, router_delete_face, router_faces_list

from DB.users_logs_DB import initialize_user_and_logs_database
from DB.face_DB import initialize_face_db

from fastapi import FastAPI,Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exception_handlers import http_exception_handler
import uvicorn

import os
import time
import threading
import asyncio
from starlette.exceptions import HTTPException as StarletteHTTPException

log_event("info", "Script starting (main.py)")
# --------------------SERVER CONFIG-------------------------------
app = FastAPI()


origins = [ "https://localhost:8123", "https://127.0.0.1:8123", "https://192.168.1.195:8123" ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], )

# -----------------------STARTUP----------------------------------------
@app.on_event("startup")
async def startup_event():
    startup_retry = 0
    while startup_retry < 5:
        try:
            # Ensure necessary directories exist
            os.makedirs(f"{VIDEO_FOLDER}", exist_ok=True)
            os.makedirs(f"{LOG_DIR}", exist_ok=True)
            # Initialize databases
            if not os.path.exists(SC_DB_PATH) or not os.path.exists(USER_LOG_DB_PATH):
                await asyncio.to_thread(initialize_user_and_logs_database)
                await asyncio.to_thread(initialize_face_db)
                log_event("info", "Databases initialized if not exists (main.py)")
            break # Exit loop if setup successful
        except Exception as e:
            startup_retry += 1
            log_event("critical", f"Failure at (main.py) startup logic (Attempt {startup_retry}/5): {e}", exc_info=True)
            await asyncio.sleep(5)  # Prevent spamming retries
    if startup_retry == 5:
        log_event("critical", "Startup at (main.py) failed after 5 attempts. Exiting program.")
        exit(1)  # Stop execution if startup fails

# -----------------------SHUTDOWN----------------------------------------
@app.on_event("shutdown")
async def shutdown_event():
    log_event("info", "App shutting down, calling camera cleanup...")
    try:
        # Directly await your imported async cleanup function
        await cleanup_camera_resources()
        log_event("info", "Shutdown process of Camera cleanup function finished (main.py).")
    except Exception as e:
        log_event("critical", f"Error calling cleanup_camera_resources during shutdown (main.py): {e}", exc_info=True)

# ---------------------APP CONFIG-------------------------------------
retry_camera = 0
retry_recognition = 0
retry_brightness = 0 

# Start camera threads with retry logic
while retry_camera < 5:
    try:
        camera_thread = threading.Thread(target=camera_feed_function, daemon=True)
        camera_thread.start()
        log_event("info", "Camera feed thread started (main.py)")
        break  # Exiting loop after success
    except Exception as e:
        retry_camera += 1
        log_event("critical", f"Failed to start camera thread (main.py) (Attempt {retry_camera}/5): {e}", exc_info=True)
        time.sleep(5)
if retry_camera == 5:
    log_event("critical", "Camera feed Thread start (main.py) failed after 5 attempts. Exiting program.")
    exit(1)  # Prevents running without the camera

# Start recognition thread with retry logic
while retry_recognition < 5:
    try:
        recognition_thread = threading.Thread(target=recognize_face, daemon=True)
        recognition_thread.start()
        log_event("info", "Face recognition thread started (main.py)")
        break  # Exit loop if successful
    except Exception as e:
        retry_recognition += 1
        log_event("critical", f"Failed to start face recognition thread (main.py) (Attempt {retry_recognition}/5): {e}", exc_info=True)
        time.sleep(5)
if retry_recognition == 5:
    log_event("critical", "Face recognition Thread (main.py) start failed after 5 attempts. Exiting program.")
    exit(1)  # Exit program and Prevents running without face recognition
time.sleep(1)
# start nightvision check thread after 1 second delay (to prevent unecessry failure)
while retry_brightness < 5:
    try:
        brightness_thread = threading.Thread(target=monitor_brightness, daemon=True)
        brightness_thread.start()
        log_event("info", "Monitor_brightness thread started (main.py)")
        break  # Exit loop if successful
    except Exception as e:
        retry_brightness += 1
        log_event("critical", f"Failed to start monitor_brightness thread (main.py) (Attempt {retry_brightness}/5): {e}", exc_info=True)
        time.sleep(5)
if retry_brightness == 5:
    log_event("critical", "Monitor_brightness thread (main.py) start failed after 5 attempts. Continuing program, PLEASE FIX.")
  
log_event("info", "starting routers after threads (main.py)")
app.include_router(router_login_and_generate_token)
# ---
app.include_router(router_livefeed)
# ---
app.include_router(router_videos_list)
app.include_router(router_video_download)
app.include_router(router_delete_video)
# ---
app.include_router(router_register_livefeed)
app.include_router(router_register_user)
app.include_router(router_delete_user)
app.include_router(router_deactivate_user)
app.include_router(router_activate_user)
app.include_router(router_user_list)
# ---
app.include_router(router_get_event_logs)
# ---
app.include_router(router_register_face)
app.include_router(router_delete_face)
app.include_router(router_faces_list)

# Global exception handler for Method errors
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 405:
        log_event("error", "Method not allowed for endpoint: Unauthorized method access", request)
    return await http_exception_handler(request, exc)

app.mount("/", StaticFiles(directory="static", html=True), name="static") #The mount have to be after the application fastapi setup+config to work or else does CORS error

if __name__ == "__main__":
    log_event("info", "main block started if python main called directly [not through CLI uvicorn] (main.py - if __main__)")
            # Start server
    uvicorn.run(app, host="0.0.0.0", port=8123, ssl_keyfile="certs/key.pem", ssl_certfile="certs/cert.pem")
    
# -------- FOR ROUTE DEBUGGING ----------------
# for route in app.routes:
#     methods = getattr(route, "methods", None)
#     path = getattr(route, "path", None)
#     name = getattr(route, "name", None)
#     log_event("info",f"Path: {path}, Methods: {methods}, Name: {name}")