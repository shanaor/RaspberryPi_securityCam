from dotenv import load_dotenv
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) #path to project root folder

load_dotenv(os.path.join(BASE_DIR, "config", ".env"))  # Loads .env file
# --------------- ENV ------------------
SECRET_KEY = os.getenv("SECRET_KEY")  # Retrieves from .env
if not SECRET_KEY:
    raise ValueError("SECRET_KEY is missing from .env file")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")  # Retrieves from .env
if not ADMIN_PASSWORD:
    raise ValueError("ADMIN_PASSWORD is missing from .env file")
ADMIN_USERNAME= os.getenv("ADMIN_USERNAME")  # Retrieves from .env
if not ADMIN_USERNAME:
    raise ValueError("ADMIN_USERNAME is missing from .env file")
# ------------- DATABASE ----------------
SC_DB_PATH = os.path.join(BASE_DIR, "DB", "security_cam.db")
USER_LOG_DB_PATH = os.path.join(BASE_DIR, "DB", "security_cam_users_logs.db")
#  ------------- FOLDERS ---------------
VIDEO_FOLDER = os.path.join(BASE_DIR, "recordings")
CONFIG_BACKUP_DIR = os.path.join(BASE_DIR, "config", "backups", "config")
LOG_DIR = os.path.join(BASE_DIR, "config", "logs") 

#  -------------- DAY_NIGHT_LOGS ------------------
BRIGHTNESS_LOG_FILE = "camera_brightness_log.txt" # to track day and night 
CONFIGTXT = "/boot/firmware/config.txt"
BRIGHTNESS_THRESHOLD = 300  # Threshold for night vision activation // Adjusted based on testing
#  -------------- DAY_NIGHT_CONFIG_BACKUP ------------------
MAX_BACKUP_DIR_SIZE_MB = 2000
TARGET_BACKUP_DIR_SIZE_MB = 100
BYTES_IN_MB = 1024 * 1024
#  ------------- TOKEN ---------------------
TOKEN_EXPIRATION_HOURS = 12
#  ---------- FRAMES -------------
FRAMES_PER_SECOND = 20
FRAME_TIME_INTERVAL = 1/FRAMES_PER_SECOND # --> 0.05 
FRAME_LIMITER = 2 # to control frame flow incase CPU cant handle 20fps on recognize_face() face recognition
GRACE_PERIOD_FRAMES = 150  # Stop recording after 150 frames (~7.5 seconds at 20 FPS) if no face in camera sight
#  ------------- RECORDINGS ---------------
SD_CARD_MEMORY_LIMIT = 90 # Percentage %
FREE_PERCENTAGE_TRAGET = 20 # Percentage %

# ------------ HTTP_ERROR MESSAGES -------------------
HTTP_ERROR_DETAILS = {
    # --- 400 + 422 Bad Request ---
    "BAD_REQUEST_NO_FACE": "No face detected. TRY AGAIN. please make sure to be properly in frame, use the green square as indicature.",
    "BAD_REQUEST_CAMERA_FAIL": "Camera not accessible, REFRESH the page and try again. (press CTRL-Shift-R for hard refresh if regular refresh doesnt work)",
    "BAD_REQUEST_INVALID_IMAGE": "Invalid image data. REFRESH the page and try again. (press CTRL-Shift-R for hard refresh if regular refresh doesnt work)",
    "BAD_REQUEST_INVALID_INPUT": "Invalid input. Insert proper input as instructed. If its face capture try make face capture more accurate (enough lighting, visible face) and try again.",
    "BAD_REQUEST_NAME_EXIST": "Name: {first_name} {last_name}, already exists. Please use a different name.",
    "BAD_REQUEST_FACE_EXIST": "Face already exists in the system. Name: {first_name} {last_name}, ID: {face_id}.",
    # --- 401 Unauthorized ---
    "INVALID_CREDENTIALS": "Invalid credentials. wrong username or password.",
    "AUTH_REQUIRED": "Log in required. please log in. You will be redirected to the login page.",
    "AUTH_EXPIRED": "Access Permission needed, please log in. You will be redirected to the login page.",
    "AUTH_INVALID_TOKEN": "Invalid access, please log in. You will be redirected to the login page.",
    
    # --- 403 Forbidden ---
    "FORBIDDEN_ADMIN_ONLY": "Unauthorized access. Admin only action. You will be redirected to the Livefeed page.",
    "DISABLED_USER": "You were disabled from the system. hash it out?",
    # --- 404 Not Found ---
    "NOT_FOUND_USER_ID": "User with ID '{user_id}' not found",
    "NOT_FOUND_FACE_ID": "No face found with ID {face_id}",
    "NOT_FOUND_VIDEO_FILE": "Video not found, If expected to be existing try REFRESHING the page. (press CTRL-Shift-R for hard refresh if regular refresh doesnt work)",
    "NOT_FOUND_NO_USERS": "No registered users.",
    "NOT_FOUND_VIDEOS": "No videos found. if expected to be, REFRESH page and try again. (press CTRL-Shift-R for hard refresh if regular refresh doesnt work)",
    "NOT_FOUND_NO_LOGS": "No logs found on {day}/{month}/{year}.",
    "NOT_FOUND_FOLDER": "No recordings folder found.",

    # --- 409  conflict with the current state of the resource ---
    "USER_NAME_ALREADY_REGISTERED": "User already registered. Please use a different username.",
    
    # --- 500 Internal Server Error ---
    "SERVER_ERROR_GENERAL_EXCEPTION": "Internal Server Error. Please REFRESH the page and try again. if persists contact support. (press CTRL-Shift-R for hard refresh if regular refresh doesnt work)",
    "SERVER_ERROR_DATABASE": "Server error. REFRESH the page and try again. (press CTRL-Shift-R for hard refresh if regular refresh doesnt work)",
    "SERVER_ERROR_VALIDATION": "Error in Validation, please refresh the page and try again. (press CTRL-Shift-R for hard refresh if regular refresh doesnt work)",
    "SERVER_ERROR_TIMEOUT": "{error}, please refresh the page and try again if persists contact support. or try in different time. (press CTRL-Shift-R for hard refresh if regular refresh doesnt work).",
    "SERVER_ERROR_OPEN_CV": "Internal server picture processing error, please refresh the page and try again if persists contact support. or try in different time. (press CTRL-Shift-R for hard refresh if regular refresh doesnt work).",
}