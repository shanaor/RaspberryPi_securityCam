from config.config import USER_LOG_DB_PATH, ADMIN_PASSWORD, ADMIN_USERNAME
from python_standalones.logger import log_event

import sqlite3
import hashlib

def initialize_user_and_logs_database():
    """Creates the database tables if they don't exist."""
    try:
        with sqlite3.connect(USER_LOG_DB_PATH) as conn:
            cursor = conn.cursor()
            # Event Logs Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS event_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Registered Users Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS registered_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            # Admin Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            ''')
            # Check if admin already exists
            cursor.execute("SELECT * FROM admin WHERE username = ?", (ADMIN_USERNAME,))
            if cursor.fetchone() is None:
                hashed_password = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()
                cursor.execute("INSERT INTO admin (username, password) VALUES (?, ?)", (ADMIN_USERNAME, hashed_password))
            conn.commit()
        log_event("info","Database initialized successfully (users_logs_DB.py).")
    except sqlite3.Error as e:
        log_event("critical", f"user_and_logs database initialization error (users_logs_DB.py): {e}")
        raise