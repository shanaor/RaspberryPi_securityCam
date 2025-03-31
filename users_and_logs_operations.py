from config.config import USER_LOG_DB_PATH
from config.models import  UserAuthorization

from python_standalones.logger import log_event
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
        with sqlite3.connect(USER_LOG_DB_PATH) as conn:
            cursor = conn.cursor()
            # Check if username already exists
            cursor.execute("SELECT * FROM registered_users WHERE username = ?", (user.username,))
            if cursor.fetchone():
                log_event("error", f"User accessed register_user function (users_and_logs_operations.py), {user.username} already exists",request) # type: ignore
                raise HTTPException(status_code=400, detail="User already exists")
            # Hash password before saving
            hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
            # Insert new user
            cursor.execute("INSERT INTO registered_users (username, password) VALUES (?, ?)", (user.username, hashed_password))
            conn.commit()
        log_event("info", f"User accessed register_user function (users_and_logs_operations.py), registered {user.username} ",request) # type: ignore
        return {"message": f"User '{user.username}' registered successfully"}
    except Exception as e:
        log_event("critical", f"register_user function error (users_and_logs_operations.py): {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
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
                log_event("error", f"User accessed delete_user function (users_and_logs_operations.py), No users with id {user_id} found to delete",request) # type: ignore
                raise HTTPException(status_code=404, detail=f"User with ID '{user_id}' not found")
            # Delete the user
            cursor.execute("DELETE FROM registered_users WHERE id = ?", (user_id,))
            conn.commit()
        log_event("warning", f"User accessed delete_user function (users_and_logs_operations.py) and deleted {user_id}",request) # type: ignore
        return{"message": f"User with ID '{user_id}' deleted successfully."}
    except Exception as e:
        log_event("critical", f"delete_user function error (users_and_logs_operations.py): {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
        
router_deactivate_user = APIRouter()
@router_deactivate_user.put("/deactivate/{user_id}/")
@authenticate_admin
def deactivate_user(user_id: int = Path(..., title="User ID", description="ID must be a positive integer", ge=1)):
    """Deactivates a user (sets is_active to 0) """
    try:
        with sqlite3.connect(USER_LOG_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM registered_users WHERE id = ?", (user_id,))
            if cursor.fetchone()[0] == 0:
                raise HTTPException(status_code=404, detail=f"User with ID '{user_id}' not found")
            cursor.execute("UPDATE registered_users SET is_active = 0 WHERE id = ?", (user_id,))
            conn.commit()
        log_event("warning", f"User accessed deactivate_user function (users_and_logs_operations.py) and deactivated {user_id} ",request) # type: ignore
        return {"message": f"User with ID '{user_id}' has been deactivated."}
    except Exception as e:
        log_event("critical", f"deactivate_user function error (users_and_logs_operations.py): {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
        
router_activate_user = APIRouter()
@router_activate_user.put("/activate/{user_id}/")
@authenticate_admin
def activate_user(user_id: int = Path(..., title="User ID", description="ID must be a positive integer", ge=1)):
    """Activates a user (sets is_active to 1) """
    try:
        with sqlite3.connect(USER_LOG_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM registered_users WHERE id = ?", (user_id,))
            if cursor.fetchone()[0] == 0:
                raise HTTPException(status_code=404, detail=f"User with ID '{user_id}' not found")
            cursor.execute("UPDATE registered_users SET is_active = 1 WHERE id = ?", (user_id,))
            conn.commit()
        log_event("info", f"User accessed activate_user function and activated {user_id} (users_and_logs_operations.py)",request) # type: ignore
        return {"message": f"User with ID '{user_id}' has been activated."}
    except Exception as e:
        log_event("critical", f"activate_user function error (users_and_logs_operations.py): {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
        
router_user_list = APIRouter()
@router_user_list.get("/userslist/")
@authenticate_admin
def get_user_list():
    """Fetch all registered users and their IDs """
    try:
        with sqlite3.connect(USER_LOG_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, is_active FROM registered_users")
            users = cursor.fetchall()
        if not users:
            log_event("error", "User accessed get_user_list function (users_and_logs_operations.py), No registered users found",request) # type: ignore
            raise HTTPException(status_code=404, detail="No registered users found.")
        log_event("info", "User accessed get_user_list function (users_and_logs_operations.py), listed registered users",request) # type: ignore
        return users
    except Exception as e:
        log_event("critical", f"get_user_list function error (users_and_logs_operations.py): {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
# --------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------
router_get_event_logs = APIRouter()
@router_get_event_logs.get("/event-logs/")
@authenticate_admin
def get_event_logs(day=None, month=None, year=None):
    """Retrieves event logs with optional date filters """
    try:
        with sqlite3.connect(USER_LOG_DB_PATH) as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM event_logs WHERE 1=1"
            params = []
            
            try:
                if day is not None:
                    day = int(day)
                    if not 1 <= day <= 31:
                        raise ValueError("Day must be an integer between 1 and 31")
                    query += " AND strftime('%d', created_at) = ?"
                    params.append(f"{day:02d}")

                if month is not None:
                    month = int(month)
                    if not 1 <= month <= 12:
                        raise ValueError("Month must be an integer between 1 and 12")
                    query += " AND strftime('%m', created_at) = ?"
                    params.append(f"{month:02d}")

                if year is not None:
                    year = int(year)
                    if not 1900 <= year <= 2100:
                        raise ValueError("Year must be an integer between 1900 and 2100")
                    query += " AND strftime('%Y', created_at) = ?"
                    params.append(str(year))
                
            except ValueError as e:
                  raise HTTPException(status_code=400, detail=str(e))

            # Execute the query with validated parameters
            cursor.execute(query, params)
            logs = cursor.fetchall()
        
        if not logs:
            log_event("error", f"User accessed get_event_logs function (users_and_logs_operations.py), {day}/{month}/{year}, No logs found.",request) # type: ignore
            raise HTTPException(status_code=404, detail=f"No logs found on {day}/{month}/{year}.")
        log_event("warning", f"User accessed get_event_logs function (users_and_logs_operations.py), {day}/{month}/{year}, listed logs",request) # type: ignore
        return logs
    except Exception as e:
        log_event("critical", f"get_event_logs function error (users_and_logs_operations.py): {e}")
        raise HTTPException(status_code=500, detail="Internal server error")