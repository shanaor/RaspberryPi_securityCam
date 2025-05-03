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
#  ------------- TOKEN ---------------------
TOKEN_EXPIRATION_HOURS = 12
#  ---------- FRAMES -------------
FRAMES_PER_SECOND = 20
FRAME_TIME_INTERVAL = 1/FRAMES_PER_SECOND # --> 0.05 
FRAME_LIMITER = 2 # to control frame flow incase CPU cant handle 20fps on recognize_face() face recognition
#  ------------- RECORDINGS ---------------
SD_CARD_MEMORY_LIMIT = 90 # Percentage %
FREE_PERCENTAGE_TRAGET = 20 # Percentage %

# ------------ HTTP_ERROR MESSAGES -------------------
HTTP_ERROR_DETAILS = {
    # --- 400 + 422 Bad Request ---
    "BAD_REQUEST_NO_FACE": "No face detected. TRY AGAIN. please make sure to be properly in frame, use the green square as indicature.",
    "BAD_REQUEST_CAMERA_FAIL": "Camera not accessible, REFRESH the page and try again. (press CTRL-Shift-R for hard refresh if regular refresh doesnt work)",
    "BAD_REQUEST_INVALID_IMAGE": "Invalid image data. REFRESH the page and try again. (press CTRL-Shift-R for hard refresh if regular refresh doesnt work)",
    "BAD_REQUEST_INVALID_INPUT": "Invalid input. Insert proper input as instructed. If its face capture try make face capture more accurate and try again.",
    
    # --- 401 Unauthorized ---
    "INVALID_CREDENTIALS": "Invalid credentials. wrong username or password.",
    "AUTH_REQUIRED": "Log in required. please log in. You will be redirected to the login page.",
    "AUTH_EXPIRED": "Access Permission needed, please log in. You will be redirected to the login page.",
    "AUTH_INVALID_TOKEN": "Invalid access, please log in. You will be redirected to the login page.",
    
    # --- 403 Forbidden ---
    "FORBIDDEN_ADMIN_ONLY": "Unauthorized access. Admin only action. You will be redirected to the Livefeed page.",
    "DISABLED_USER": "You were unauthorized from the system. hash it out?",
    # --- 404 Not Found ---
    "NOT_FOUND_USER_ID": "User with ID '{user_id}' not found",
    "NOT_FOUND_FACE_ID": "No face found with ID {face_id}",
    "NOT_FOUND_VIDEO_FILE": "Video not found, If expected to be existing try REFRESHING the page. (press CTRL-Shift-R for hard refresh if regular refresh doesnt work)",
    "NOT_FOUND_NO_USERS": "No registered users.",
    "NOT_FOUND_NO_VIDEOS_LIST": "No videos list found, if expected to be, REFRESH page and try again. (press CTRL-Shift-R for hard refresh if regular refresh doesnt work)",
    "NOT_FOUND_NO_LOGS": "No logs found on {day}/{month}/{year}.",
    "NOT_FOUND_FOLDER": "No recordings folder found.",

    # --- 409  conflict with the current state of the resource ---
    "USER_NAME_ALREADY_REGISTERED": "User already registered. Please use a different username.",
    
    # --- 500 Internal Server Error ---
    "SERVER_ERROR_GENERAL_EXCEPTION": "Internal Server Error. Please REFRESH the page and try again. if persists contact support. (press CTRL-Shift-R for hard refresh if regular refresh doesnt work)",
    "SERVER_ERROR_DATABASE": "Database error. REFRESH the page and try again. (press CTRL-Shift-R for hard refresh if regular refresh doesnt work)",
    "SERVER_ERROR_VALIDATION": "Error in Validation, please refresh the page and try again. (press CTRL-Shift-R for hard refresh if regular refresh doesnt work)",
    "SERVER_ERROR_TIMEOUT": "{error}, please refresh the page and try again if persists contact support. or try in different time. (press CTRL-Shift-R for hard refresh if regular refresh doesnt work).",
}