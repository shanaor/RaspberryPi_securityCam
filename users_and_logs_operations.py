from python_standalones.logger import log_event
from config.config import USER_LOG_DB_PATH
from config.models import  UserAuthorization
from login import authenticate_admin

import sqlite3
import hashlib
from fastapi import APIRouter,HTTPException,Path

""""""""""""""""""""""""""""""""""""
""""""""" ADMIN TERRITORY """""""""
""""""""""""""""""""""""""""""""""""
router_register_user = APIRouter()
@router_register_user.post("/register_user/")
@authenticate_admin
def register_user(user: UserAuthorization):
    """ Register a new user """
    try:    
        conn = sqlite3.connect(USER_LOG_DB_PATH)
        cursor = conn.cursor()
        # Check if username already exists
        cursor.execute("SELECT * FROM registered_users WHERE username = ?", (user.username,))
        if cursor.fetchone():
            conn.close()
            log_event("error", f"User accessed /register_user, {user.username} already exists",request) # type: ignore
            raise HTTPException(status_code=400, detail="User already exists")
        # Hash password before saving
        hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
        # Insert new user
        cursor.execute("INSERT INTO registered_users (username, password) VALUES (?, ?)", (user.username, hashed_password))
        conn.commit()
        conn.close()
        log_event("info", f"User accessed /register_user, registered {user.username} ",request) # type: ignore
        return {"message": f"User '{user.username}' registered successfully"}
    except Exception as e:
        log_event("critical", f"register_user function error at users_and_logs_operations.py: {e}")
# --------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------
router_delete_user = APIRouter()
@router_delete_user.delete("/delete/{user_id}/")
@authenticate_admin
def delete_user(user_id: int = Path(..., title="User ID", description="ID must be a positive integer", ge=1)):
    """Deletes a user from the registered_users table """
    try:
        with sqlite3.connect(USER_LOG_DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Check if the user exists first
            cursor.execute("SELECT COUNT(*) FROM registered_users WHERE id = ?", (user_id,))
            user_count = cursor.fetchone()[0]
            if user_count == 0:
                log_event("error", f"User accessed /delete at users_and_logs_operations.py, No users with id {user_id} found to delete",request) # type: ignore
                raise HTTPException(status_code=404, detail=f"User with ID '{user_id}' not found")
        
            # Delete the user
            cursor.execute("DELETE FROM registered_users WHERE id = ?", (user_id,))
            conn.commit()
        log_event("warning", f"User accessed /delete at users_and_logs_operations.py and deleted {user_id}",request) # type: ignore
        return{"message": f"User with ID '{user_id}' deleted successfully."}
    
    except HTTPException as he: # Re-raise HTTP exceptions (like the 404)
        raise he
    except Exception as e:
        log_event("critical", f"delete_user function error at users_and_logs_operations.py: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
        
router_deactivate_user = APIRouter()
@router_deactivate_user.put("/deactivate/{user_id}/")
@authenticate_admin
def deactivate_user(user_id: int = Path(..., title="User ID", description="ID must be a positive integer", ge=1)):
    """Deactivates a user (sets is_active to 0) """
    try:
        conn = sqlite3.connect(USER_LOG_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE registered_users SET is_active = 0 WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        log_event("warning", f"User accessed /deactivate at users_and_operations.py and deactivated {user_id} ",request) # type: ignore
        return {"message": f"User with ID '{user_id}' has been deactivated."}
    except Exception as e:
        log_event("critical", f"deactivate_user function error at users_and_logs_operations.py: {e}")
        
router_activate_user = APIRouter()
@router_activate_user.put("/activate/{user_id}/")
@authenticate_admin
def activate_user(user_id: int = Path(..., title="User ID", description="ID must be a positive integer", ge=1)):
    """Activates a user (sets is_active to 1) """
    try:
        conn = sqlite3.connect(USER_LOG_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE registered_users SET is_active = 1 WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        log_event("info", f"User accessed /activate and activated {user_id}",request) # type: ignore
        return {"message": f"User with ID '{user_id}' has been activated."}
    except Exception as e:
        log_event("critical", f"activate_user function error at users_and_logs_operations.py: {e}")
        
router_user_list = APIRouter()
@router_user_list.get("/userslist/")
@authenticate_admin
def get_user_list():
    """Fetch all registered users and their IDs """
    try:
        conn = sqlite3.connect(USER_LOG_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, is_active FROM registered_users")
        users = cursor.fetchall()
        conn.close()

        if not users:
            log_event("error", "User accessed /userslist at users_and_operations.py, No registered users found",request) # type: ignore
            raise HTTPException(status_code=404, detail="No registered users found.")
        log_event("info", "User accessed /userslist, listed registered users",request) # type: ignore
        return users
    except Exception as e:
        log_event("critical", f"get_user_list function error at users_and_logs_operations.py: {e}")
# --------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------
router_get_event_logs = APIRouter()
@router_get_event_logs.get("/event-logs/")
@authenticate_admin
def get_event_logs(day=None, month=None, year=None):
    """Retrieves event logs with optional date filters """
    try:
        conn = sqlite3.connect(USER_LOG_DB_PATH)
        cursor = conn.cursor()

        query = "SELECT * FROM event_logs WHERE 1=1"
        params = []
        if day:
            query += " AND strftime('%d', created_at) = ?"
            params.append(f"{int(day):02d}")
        if month:
            query += " AND strftime('%m', created_at) = ?"
            params.append(f"{int(month):02d}")
        if year:
            query += " AND strftime('%Y', created_at) = ?"
            params.append(str(year))
        
        cursor.execute(query, params)
        logs = cursor.fetchall()
        conn.close()
        if not logs:
            log_event("error", f"User accessed /event-logs at users_and_operations.py, {day}/{month}/{year}, No logs found.",request) # type: ignore
            raise HTTPException(status_code=404, detail=f"No logs found on {day}/{month}/{year}.")
        log_event("warning", f"User accessed /event-logs, {day}/{month}/{year}, listed logs",request) # type: ignore
        return logs
    except Exception as e:
        log_event("critical", f"get_event_logs function error at users_and_logs_operations.py: {e}")