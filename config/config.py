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