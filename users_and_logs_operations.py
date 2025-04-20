from config.config import HTTP_ERROR_DETAILS, USER_LOG_DB_PATH
from config.models import UserAuthorization

from python_standalones.logger import log_event
from login import authenticate_user

from fastapi import APIRouter,HTTPException,Path,Depends,Request
import sqlite3

import hashlib

""""""""""""""""""""""""""""""""""""
""""" ADMIN TERRITORY ONLY """""""""
""""""""""""""""""""""""""""""""""""
router_register_user = APIRouter()
@router_register_user.post("/register_user/")
def register_user(user: UserAuthorization,request:Request,current_user: dict = Depends(authenticate_user)):
    """ Register a new user to use the system """
    try: 
        is_admin = current_user.get("is_admin")
        frontend_user_id = current_user.get("user_id")
        if not is_admin:
            log_event("error", f"User accessed register_user function (users_and_logs_operations.py), admin privileges required. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
            raise HTTPException(status_code=403, detail=HTTP_ERROR_DETAILS["FORBIDDEN_ADMIN_ONLY"])
        
        with sqlite3.connect(USER_LOG_DB_PATH) as conn:
            cursor = conn.cursor()
            # Check if username already exists
            cursor.execute("SELECT * FROM registered_users WHERE username = ?", (user.username,))
            if cursor.fetchone():
                log_event("error", f"User accessed register_user function (users_and_logs_operations.py), {user.username} already exists. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
                raise HTTPException(status_code=409, detail=HTTP_ERROR_DETAILS["USER_NAME_ALREADY_REGISTERED"])
            # Hash password before saving
            hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
            # Insert new user
            cursor.execute("INSERT INTO registered_users (username, password) VALUES (?, ?)", (user.username, hashed_password))
            conn.commit()
        log_event("info", f"User accessed register_user function (users_and_logs_operations.py), registered {user.username}. accessed by admin status:{is_admin}, user:{frontend_user_id} ",request)
        return {"message": f"User '{user.username}' registered successfully"}
    except HTTPException:
        raise
    except sqlite3.Error as e:
        log_event("error", f"Database error in register_user function (users_and_logs_operations.py): {e}. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_DB_EXCEPTION"])
    except ValueError as e:
        log_event("error", f"Value error in register_user function (users_and_logs_operations.py): {e}. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_event("critical", f"register_user function error (users_and_logs_operations.py): {e}. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_GENERAL_EXCEPTION"])
# --------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------
router_delete_user = APIRouter()
@router_delete_user.delete("/delete/{user_id}/")
def delete_user(request:Request,current_user: dict = Depends(authenticate_user),
                user_id: int = Path(..., title="User ID", description="ID must be a positive integer", ge=1)):
    """Deletes a user from the registered_users table """
    try:
        is_admin = current_user.get("is_admin")
        frontend_user_id = current_user.get("user_id")
        if not is_admin:
            log_event("error", f"User accessed delete_user function (users_and_logs_operations.py), admin privileges required. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
            raise HTTPException(status_code=403, detail=HTTP_ERROR_DETAILS["FORBIDDEN_ADMIN_ONLY"])
        
        # Check if the user exists
        with sqlite3.connect(USER_LOG_DB_PATH) as conn:
            cursor = conn.cursor() 
            cursor.execute("SELECT COUNT(*) FROM registered_users WHERE id = ?", (user_id,))
            user_count = cursor.fetchone()[0]
            if user_count == 0:
                log_event("error", f"User accessed delete_user function (users_and_logs_operations.py), No users with id {user_id} found to delete. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
                raise HTTPException(status_code=404, detail=HTTP_ERROR_DETAILS["NOT_FOUND_USER_ID"].format(user_id=user_id))
            # Delete the user
            cursor.execute("DELETE FROM registered_users WHERE id = ?", (user_id,))
            conn.commit()
        log_event("warning", f"User accessed delete_user function (users_and_logs_operations.py) and deleted {user_id}. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
        return{"message": f"User with ID '{user_id}' deleted successfully."}
    except HTTPException:
        raise
    except sqlite3.Error as e:
        log_event("error", f"Database error in delete_user function (users_and_logs_operations.py): {e}. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_DB_EXCEPTION"])
    except Exception as e:
        log_event("critical", f"delete_user function error (users_and_logs_operations.py): {e}. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_GENERAL_EXCEPTION"])
        
router_deactivate_user = APIRouter()
@router_deactivate_user.put("/deactivate/{user_id}/")
def deactivate_user(request:Request,current_user: dict = Depends(authenticate_user),
                    user_id: int = Path(..., title="User ID", description="ID must be a positive integer", ge=1)):
    """Deactivates a user (sets is_active to 0) """
    try:
        is_admin = current_user.get("is_admin")
        frontend_user_id = current_user.get("user_id")
        if not is_admin:
            log_event("error", f"User accessed deactivate_user function (users_and_logs_operations.py), admin privileges required. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
            raise HTTPException(status_code=403, detail=HTTP_ERROR_DETAILS["FORBIDDEN_ADMIN_ONLY"])
        
        with sqlite3.connect(USER_LOG_DB_PATH) as conn:
            cursor = conn.cursor()
            # Check if the user exists
            cursor.execute("SELECT COUNT(*) FROM registered_users WHERE id = ?", (user_id,))
            if cursor.fetchone()[0] == 0:
                raise HTTPException(status_code=404, detail=HTTP_ERROR_DETAILS["NOT_FOUND_USER_ID"].format(user_id=user_id))
            # Deactivate the user
            cursor.execute("UPDATE registered_users SET is_active = 0 WHERE id = ?", (user_id,))
            conn.commit()
        log_event("warning", f"User accessed deactivate_user function (users_and_logs_operations.py) and deactivated {user_id}. accessed by admin status:{is_admin}, user:{frontend_user_id} ",request)
        return {"message": f"User with ID '{user_id}' has been deactivated."}
    except HTTPException:
        raise
    except sqlite3.Error as e:
        log_event("error", f"Database error in deactivate_user function (users_and_logs_operations.py): {e}. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_DB_EXCEPTION"])
    except Exception as e:
        log_event("critical", f"deactivate_user function error (users_and_logs_operations.py): {e}. accessed by Admin status:{is_admin}, user:{frontend_user_id}):",request)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_GENERAL_EXCEPTION"])
        
router_activate_user = APIRouter()
@router_activate_user.put("/activate/{user_id}/")
def activate_user(request:Request,current_user: dict = Depends(authenticate_user),
                  user_id: int = Path(..., title="User ID", description="ID must be a positive integer", ge=1)):
    """Activates a user (sets is_active to 1) """
    try:
        is_admin = current_user.get("is_admin")
        frontend_user_id = current_user.get("user_id")
        if not is_admin:
            log_event("error", f"User accessed activate_user function (users_and_logs_operations.py), admin privileges required. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
            raise HTTPException(status_code=403, detail=HTTP_ERROR_DETAILS["FORBIDDEN_ADMIN_ONLY"])
        
        with sqlite3.connect(USER_LOG_DB_PATH) as conn:
            cursor = conn.cursor()
            # Check if the user exists
            cursor.execute("SELECT COUNT(*) FROM registered_users WHERE id = ?", (user_id,))
            if cursor.fetchone()[0] == 0:
                log_event("error", f"User accessed activate_user function (users_and_logs_operations.py), No users with id {user_id} found to activate. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
                raise HTTPException(status_code=404, detail=HTTP_ERROR_DETAILS["NOT_FOUND_USER_ID"].format(user_id=user_id))
            # Activate the user
            cursor.execute("UPDATE registered_users SET is_active = 1 WHERE id = ?", (user_id,))
            conn.commit()
        log_event("info", f"User accessed activate_user function and activated {user_id} (users_and_logs_operations.py). accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
        return {"message": f"User with ID '{user_id}' has been activated."}
    except HTTPException:
        raise
    except sqlite3.Error as e:
        log_event("error", f"Database error in activate_user function (users_and_logs_operations.py): {e}. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_DB_EXCEPTION"])
    except Exception as e:
        log_event("critical", f"activate_user function error (users_and_logs_operations.py): {e}. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_GENERAL_EXCEPTION"])
        
router_user_list = APIRouter()
@router_user_list.get("/userslist/")
def get_user_list(request:Request,current_user: dict = Depends(authenticate_user)):
    """Fetch all registered users and their IDs """
    try:
        is_admin = current_user.get("is_admin")
        frontend_user_id = current_user.get("user_id")
        if not is_admin:
            log_event("error", f"User accessed get_user_list function (users_and_logs_operations.py), admin privileges required. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
            raise HTTPException(status_code=403, detail=HTTP_ERROR_DETAILS["FORBIDDEN_ADMIN_ONLY"])
        
        with sqlite3.connect(USER_LOG_DB_PATH) as conn:
            cursor = conn.cursor()
            # Check if the users table exists
            cursor.execute("SELECT id, username, is_active FROM registered_users")
            users = cursor.fetchall()
        # Check if users not found
        if not users:
            log_event("error", f"User accessed get_user_list function (users_and_logs_operations.py), No registered users found. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
            raise HTTPException(status_code=404, detail=HTTP_ERROR_DETAILS["NOT_FOUND_NO_USERS"])
        log_event("info", f"User accessed get_user_list function (users_and_logs_operations.py), listed registered users. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
        return users
    except HTTPException:
        raise
    except sqlite3.Error as e:
        log_event("error", f"Database error in get_user_list function (users_and_logs_operations.py): {e}. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_DB_EXCEPTION"])
    except Exception as e:
        log_event("critical", f"get_user_list function error (users_and_logs_operations.py): {e}. accessed by admin status:{is_admin}, user:{frontend_user_id}", request)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_GENERAL_EXCEPTION"])
# --------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------
router_get_event_logs = APIRouter()
@router_get_event_logs.get("/event-logs/")
def get_event_logs(request:Request,current_user: dict = Depends(authenticate_user),day=None, month=None, year=None):
    """Retrieves event logs with optional date filters """
    try:
        is_admin = current_user.get("is_admin")
        frontend_user_id = current_user.get("user_id")
        if not is_admin:
            log_event("error", f"User accessed get_event_logs function (users_and_logs_operations.py), admin privileges required. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
            raise HTTPException(status_code=403, detail=HTTP_ERROR_DETAILS["FORBIDDEN_ADMIN_ONLY"])
        
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
            log_event("error", f"User accessed get_event_logs function (users_and_logs_operations.py), {day}/{month}/{year}, No logs found. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
            raise HTTPException(status_code=404, detail=HTTP_ERROR_DETAILS["NOT_FOUND_NO_LOGS"].format(day=day, month=month, year=year))
        log_event("warning", f"User accessed get_event_logs function (users_and_logs_operations.py), {day}/{month}/{year}, listed logs. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
        return logs
    except HTTPException:
        raise
    except ValueError as e:
        log_event("error", f"Value error in get_event_logs function (users_and_logs_operations.py): {e}. accessed by admin status:{is_admin}, user:{frontend_user_id}")
        raise HTTPException(status_code=400, detail=str(e))
    except sqlite3.Error as e:
        log_event("error", f"Database error in get_event_logs function (users_and_logs_operations.py): {e}. accessed by admin status:{is_admin}, user:{frontend_user_id}")
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_DB_EXCEPTION"])
    except Exception as e:
        log_event("critical", f"get_event_logs function error (users_and_logs_operations.py): {e}. accessed by admin status:{is_admin}, user:{frontend_user_id}")
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_GENERAL_EXCEPTION"])