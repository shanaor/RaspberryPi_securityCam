from config.config import SC_DB_PATH
from python_standalones.logger import log_event

import sqlite3

def initialize_face_db():
    """Creates the face registration table if it doesn't exist."""
    try:
        with sqlite3.connect(SC_DB_PATH) as conn:
            cursor = conn.cursor()

            # Create table for storing face encodings
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS registered_faces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    encoding BLOB NOT NULL,
                    encoding_hash REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
        log_event("info","Face database initialized successfully.")
    except sqlite3.Error as e:
        log_event("critical", f"Face database initialization error at face_DB.py: {e}") 
        raise