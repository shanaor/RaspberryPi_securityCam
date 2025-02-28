from dotenv import load_dotenv
import os

load_dotenv("config\.env")  # Loads .env file
SECRET_KEY = os.getenv("SECRET_KEY")  # Retrieves from .env
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")  # Retrieves from .env
ADMIN_USERNAME= os.getenv("ADMIN_USERNAME")  # Retrieves from .env

VIDEO_FOLDER = "recordings"
SC_DB_PATH = "security_cam.db"
USER_LOG_DB_PATH = "security_cam_users_logs.db"