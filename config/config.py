from dotenv import load_dotenv
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) #path to project root folder

load_dotenv(os.path.join(BASE_DIR, "config", ".env"))  # Loads .env file
# ---------------------------------
SECRET_KEY = os.getenv("SECRET_KEY")  # Retrieves from .env
if not SECRET_KEY:
    raise ValueError("SECRET_KEY is missing from .env file")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")  # Retrieves from .env
if not ADMIN_PASSWORD:
    raise ValueError("ADMIN_PASSWORD is missing from .env file")
ADMIN_USERNAME= os.getenv("ADMIN_USERNAME")  # Retrieves from .env
if not ADMIN_USERNAME:
    raise ValueError("ADMIN_USERNAME is missing from .env file")
# -----------------------------
SC_DB_PATH = os.path.join(BASE_DIR, "DB", "security_cam.db")
USER_LOG_DB_PATH = os.path.join(BASE_DIR, "DB", "security_cam_users_logs.db")
#  ----------------------------
VIDEO_FOLDER = os.path.join(BASE_DIR, "recordings")
CONFIG_BACKUP_DIR = os.path.join(BASE_DIR, "config", "backups", "config")
LOG_DIR = os.path.join(BASE_DIR, "config", "logs") 
#  --------------------------------
BRIGHTNESS_LOG_FILE = "camera_brightness_log.txt" # to track day and night 
CONFIGTXT = "/boot/firmware/config.txt"
#  ----------------------------------
TOKEN_EXPIRATION_HOURS = 12
#  -----------------------