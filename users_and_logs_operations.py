from config.config import HTTP_ERROR_DETAILS, USER_LOG_DB_PATH
from config.models import UserAuthorization

from python_standalones.logger import log_event
from login import authenticate_user

from fastapi import APIRouter,HTTPException,Path,Depends,Request
import sqlite3

import asyncio
import hashlib

""""""""""""""""""""""""""""""""""""
""""" ADMIN TERRITORY ONLY """""""""
""""""""""""""""""""""""""""""""""""
def register_DB_request(user):
    """ Checks if the username entered by the users already exists to avoid duplicates, sends upper function dictionary with True boolean.
        If name doesnt exist, registers the new name and password.
        If succeful registered the asyncio.to_thread inserts None to the name_exist variable (because no value was returned) and it would skip the If check"""
    try:
        with sqlite3.connect(USER_LOG_DB_PATH) as conn:
            cursor = conn.cursor()
            # Check if username already exists
            cursor.execute("SELECT * FROM registered_users WHERE username = ?", (user.username,))
            if cursor.fetchone():
                return {"exist": True}
            # Hash password before saving
            hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
            # Insert new user
            cursor.execute("INSERT INTO registered_users (username, password) VALUES (?, ?)", (user.username, hashed_password))
            conn.commit()
    except sqlite3.Error as e:
        raise

router_register_user = APIRouter()
@router_register_user.post("/register_user/")
async def register_user(user: UserAuthorization,request:Request,current_user: dict = Depends(authenticate_user)):
    """ Register a new user to use the system.
    get the user name and password from the frontend by Admin, using the UserAuthorization model for the regex screening.
     use asyncio.to_thread to run databse function to prevent blocking the event loop.
     check if the name already exists in the database to prevent duplicates. if exists raise HTTPException 409 error."""
    try: 
        is_admin = current_user.get("is_admin")
        frontend_user_id = current_user.get("user_id")
        if not is_admin:
            log_event("error", f"User accessed register_user function (users_and_logs_operations.py), admin privileges required. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
            raise HTTPException(status_code=403, detail=HTTP_ERROR_DETAILS["FORBIDDEN_ADMIN_ONLY"])
        
        name_exist = await asyncio.to_thread(register_DB_request,user)
        if name_exist:
            log_event("error", f"User accessed register_user function (users_and_logs_operations.py),tried register with existing name: {user.username} <-----. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
            raise HTTPException(status_code=409, detail=HTTP_ERROR_DETAILS["USER_NAME_ALREADY_REGISTERED"])
        log_event("info", f"User accessed register_user function (users_and_logs_operations.py), registered {user.username}. accessed by admin status:{is_admin}, user:{frontend_user_id} ",request)
        return {"message": f"User '{user.username}' registered successfully"}
    except HTTPException:
        raise
    except sqlite3.Error as e:
        log_event("error", f"Database error in register_DB_request function (users_and_logs_operations.py): {e}. accessed by admin status:{is_admin}, user:{frontend_user_id}",request, exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_DATABASE"])
    except ValueError as e:
        log_event("error", f"Value error in register_user function (users_and_logs_operations.py): {e}. accessed by admin status:{is_admin}, user:{frontend_user_id}",request, exc_info=True)
        raise HTTPException(status_code=400, detail=HTTP_ERROR_DETAILS["BAD_REQUEST_INVALID_INPUT"])
    except Exception as e:
        log_event("critical", f"register_user function error (users_and_logs_operations.py): {e}. accessed by admin status:{is_admin}, user:{frontend_user_id}",request, exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_GENERAL_EXCEPTION"])
# --------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------
def delete_DB_check(user_id):
    """ Checks if user ID exists in the database, if not it retrn a false boolean to the upper function.
        If ID exists it fetches the username and deletes the user from the database and returns the username and 
        True boolean on the user ID exist key to prevent the If check from failing"""
    try:        
            # Check if the user exists
        with sqlite3.connect(USER_LOG_DB_PATH) as conn:
            cursor = conn.cursor() 
            # Fetch username
            cursor.execute("SELECT username FROM registered_users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            if not result:
                return {"ID_exist": False}
            
            username = result[0]

            # Delete user
            cursor.execute("DELETE FROM registered_users WHERE id = ?", (user_id,))
            conn.commit()
            return {"username_deleted": username, "ID_exist": True}
    except sqlite3.Error as e:
        raise

router_delete_user = APIRouter()
@router_delete_user.delete("/delete/{user_id}/")
async def delete_user(request:Request,current_user: dict = Depends(authenticate_user),
                user_id: int = Path(..., title="User ID", description="ID must be a positive integer", ge=1)):
    """Deletes a user from the registered_users table.
    Used asyncio.to_thread to run the function to prevent possible block of the vent loop if database gets busy.
    checks if user ID exists, if not sends 404 error, if exists it deletes the user , logs even with deleted username and ID and return success message"""
    try:
        is_admin = current_user.get("is_admin")
        frontend_user_id = current_user.get("user_id")
        if not is_admin:
            log_event("error", f"User accessed delete_user function (users_and_logs_operations.py), admin privileges required. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
            raise HTTPException(status_code=403, detail=HTTP_ERROR_DETAILS["FORBIDDEN_ADMIN_ONLY"])
        
        # Check if the user exists
        target_user = await asyncio.to_thread(delete_DB_check,user_id)
        if target_user["ID_exist"] == False:
            log_event("error", f"User accessed delete_user function (users_and_logs_operations.py), No users with id {user_id} found to delete. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
            raise HTTPException(status_code=404, detail=HTTP_ERROR_DETAILS["NOT_FOUND_USER_ID"].format(user_id=user_id))
        deleted_user = target_user["username_deleted"]
        log_event("warning", f"User accessed delete_user function (users_and_logs_operations.py) and deleted User: {deleted_user}, ID: {user_id}. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
        return{"message": f"User: {deleted_user} with ID '{user_id}' deleted successfully."}
    except HTTPException:
        raise
    except sqlite3.Error as e:
        log_event("error", f"Database error in delete_DB_check function (users_and_logs_operations.py): {e}. accessed by admin status:{is_admin}, user:{frontend_user_id}",request, exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_DATABASE"])
    except Exception as e:
        log_event("critical", f"delete_user function error (users_and_logs_operations.py): {e}. accessed by admin status:{is_admin}, user:{frontend_user_id}",request, exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_GENERAL_EXCEPTION"])
# --------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------
def deactivate_DB_check(user_id):
    """Checks if user ID exists in the database, if not it retrn a false boolean to the upper function.
        If ID exists it fetches the username and deactivates the user from the database and returns the username and 
        True boolean on the user ID exist key to prevent the If check from failing"""
    try:
        with sqlite3.connect(USER_LOG_DB_PATH) as conn:
            cursor = conn.cursor()
            # Check if the user exists
            cursor.execute("SELECT username FROM registered_users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            if not result:
                return {"ID_exist": False}
            
            username = result[0]
            # Deactivate the user
            cursor.execute("UPDATE registered_users SET is_active = 0 WHERE id = ?", (user_id,))
            conn.commit()
            return {"deactivated_username": username, "ID_exist": True}
    except sqlite3.Error as e:
        raise

router_deactivate_user = APIRouter()
@router_deactivate_user.put("/deactivate/{user_id}/")
async def deactivate_user(request:Request,current_user: dict = Depends(authenticate_user),
                    user_id: int = Path(..., title="User ID", description="ID must be a positive integer", ge=1)):
    """Deactivates a user (sets is_active to 0). 
    asyncio.to_thread to prevent possible database blocking. same api logic as delete_user"""
    try:
        is_admin = current_user.get("is_admin")
        frontend_user_id = current_user.get("user_id")
        if not is_admin:
            log_event("error", f"User accessed deactivate_user function (users_and_logs_operations.py), admin privileges required. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
            raise HTTPException(status_code=403, detail=HTTP_ERROR_DETAILS["FORBIDDEN_ADMIN_ONLY"])
        
        # Check if the user exists
        target_user = await asyncio.to_thread(deactivate_DB_check,user_id)
        if target_user["ID_exist"] == False:
            log_event("warning", f"User accessed deactivate_user function (users_and_logs_operations.py), User: {user_id} does not exist. accessed by admin status:{is_admin}, user:{frontend_user_id} ",request)
            raise HTTPException(status_code=404, detail=HTTP_ERROR_DETAILS["NOT_FOUND_USER_ID"].format(user_id=user_id))
        deactivated_user = target_user["deactivated_username"]
        # Deactivate the user
        log_event("warning", f"User accessed deactivate_user function (users_and_logs_operations.py) and deactivated User: {deactivated_user}, ID: {user_id}. accessed by admin status:{is_admin}, user:{frontend_user_id} ",request)
        return {"message": f"User: {deactivated_user}, with ID '{user_id}' has been deactivated."}
    except HTTPException:
        raise
    except sqlite3.Error as e:
        log_event("error", f"Database error in deactivate_DB_check function (users_and_logs_operations.py): {e}. accessed by admin status:{is_admin}, user:{frontend_user_id}",request, exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_DATABASE"])
    except Exception as e:
        log_event("critical", f"deactivate_user function error (users_and_logs_operations.py): {e}. accessed by Admin status:{is_admin}, user:{frontend_user_id}):",request, exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_GENERAL_EXCEPTION"])
# --------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------
def activate_DB_check(user_id):
    """Checks if user ID exists in the database, if not it retrn a false boolean to the upper function.
        If ID exists it fetches the username and activates the user from the database and returns the username and 
        True boolean on the user ID exist key to prevent the If check from failing"""
    try:
        with sqlite3.connect(USER_LOG_DB_PATH) as conn:
            cursor = conn.cursor()
            # Check if the user exists
            cursor.execute("SELECT username FROM registered_users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            if not result:
                return {"ID_exist": False}
            
            username = result[0]
            # Activate the user
            cursor.execute("UPDATE registered_users SET is_active = 1 WHERE id = ?", (user_id,))
            conn.commit()
            return{"activated_username": username, "ID_exist": True}
    except sqlite3.Error as e:
        raise

router_activate_user = APIRouter()
@router_activate_user.put("/activate/{user_id}/")
async def activate_user(request:Request,current_user: dict = Depends(authenticate_user),
                  user_id: int = Path(..., title="User ID", description="ID must be a positive integer", ge=1)):
    """Activates a user (sets is_active to 1). 
    asyncio.to_thread to prevent possible database blocking. same api logic as delete_user"""
    try:
        is_admin = current_user.get("is_admin")
        frontend_user_id = current_user.get("user_id")
        if not is_admin:
            log_event("error", f"User accessed activate_user function (users_and_logs_operations.py), admin privileges required. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
            raise HTTPException(status_code=403, detail=HTTP_ERROR_DETAILS["FORBIDDEN_ADMIN_ONLY"])
        
        # Check if the user exists
        target_user = await asyncio.to_thread(activate_DB_check,user_id)
        if target_user["ID_exist"] == False:
            log_event("error", f"User accessed activate_user function (users_and_logs_operations.py), No users with id {user_id} found to activate. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
            raise HTTPException(status_code=404, detail=HTTP_ERROR_DETAILS["NOT_FOUND_USER_ID"].format(user_id=user_id))
        activated_user = target_user["activated_username"]
        log_event("info", f"User accessed activate_user function  (users_and_logs_operations.py) and activated User: {activated_user}, ID: {user_id}. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
        return {"message": f"User:{activated_user}, with ID '{user_id}' has been activated."}
    except HTTPException:
        raise
    except sqlite3.Error as e:
        log_event("error", f"Database error in activate_DB_check function (users_and_logs_operations.py): {e}. accessed by admin status:{is_admin}, user:{frontend_user_id}",request, exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_DATABASE"])
    except Exception as e:
        log_event("critical", f"activate_user function error (users_and_logs_operations.py): {e}. accessed by admin status:{is_admin}, user:{frontend_user_id}",request, exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_GENERAL_EXCEPTION"])
# --------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------        
def get_user_list_DB_fetch():
    """ Fetches all user lists and either returns to the upper function a list or return empty """
    try:
        with sqlite3.connect(USER_LOG_DB_PATH) as conn:
            cursor = conn.cursor()
            # Check if the users table exists
            cursor.execute("SELECT id, username, is_active FROM registered_users")
            return cursor.fetchall()
    except sqlite3.Error as e:
        raise

router_user_list = APIRouter()
@router_user_list.get("/userslist/")
async def get_user_list(request:Request,current_user: dict = Depends(authenticate_user)):
    """Fetch all registered users and their IDs.
    asyncion.to_thread to run Database funtion to prevent possible blocking."""
    try:
        is_admin = current_user.get("is_admin")
        frontend_user_id = current_user.get("user_id")
        if not is_admin:
            log_event("error", f"User accessed get_user_list function (users_and_logs_operations.py), admin privileges required. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
            raise HTTPException(status_code=403, detail=HTTP_ERROR_DETAILS["FORBIDDEN_ADMIN_ONLY"])
        
        users = await asyncio.to_thread(get_user_list_DB_fetch)
        # Check if users not found
        if not users:
            log_event("error", f"User accessed get_user_list function (users_and_logs_operations.py), No registered users found. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
            raise HTTPException(status_code=404, detail=HTTP_ERROR_DETAILS["NOT_FOUND_NO_USERS"])
        log_event("info", f"User accessed get_user_list function (users_and_logs_operations.py), listed registered users. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
        return users
    except HTTPException:
        raise
    except sqlite3.Error as e:
        log_event("error", f"Database error in get_user_list_DB_fetch function (users_and_logs_operations.py): {e}. accessed by admin status:{is_admin}, user:{frontend_user_id}",request, exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_DATABASE"])
    except Exception as e:
        log_event("critical", f"get_user_list function error (users_and_logs_operations.py): {e}. accessed by admin status:{is_admin}, user:{frontend_user_id}",request, exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_GENERAL_EXCEPTION"])
# --------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------
def logs_DB_fetch(day, month, year):
    """ gets the day, month and year from the user, checks that the value syntax is correct, then does paramas chain. 
    then fetches logs."""
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
                raise 

            # Execute the query with validated parameters
            cursor.execute(query, params)
            return cursor.fetchall()
    except sqlite3.Error as e:
        raise

router_get_event_logs = APIRouter()
@router_get_event_logs.get("/event-logs/")
async def get_event_logs(request:Request,current_user: dict = Depends(authenticate_user),day=None, month=None, year=None):
    """Retrieves event logs of the Camera recording Logs with optional date filters.
    asyncio.to_thread to run Database funciton to prevent blocking."""
    try:
        is_admin = current_user.get("is_admin")
        frontend_user_id = current_user.get("user_id")
        if not is_admin:
            log_event("error", f"User accessed get_event_logs function (users_and_logs_operations.py), admin privileges required. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
            raise HTTPException(status_code=403, detail=HTTP_ERROR_DETAILS["FORBIDDEN_ADMIN_ONLY"])
        
        logs = await asyncio.to_thread(logs_DB_fetch,day, month, year)
        
        if not logs:
            log_event("error", f"User accessed get_event_logs function (users_and_logs_operations.py), {day}/{month}/{year}, No logs found. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
            raise HTTPException(status_code=404, detail=HTTP_ERROR_DETAILS["NOT_FOUND_NO_LOGS"].format(day=day, month=month, year=year))
        log_event("warning", f"User accessed get_event_logs function (users_and_logs_operations.py), {day}/{month}/{year}, listed logs. accessed by admin status:{is_admin}, user:{frontend_user_id}",request)
        return logs
    except HTTPException:
        raise
    except ValueError as e:
        log_event("error", f"Value error in logs_DB_fetch function (users_and_logs_operations.py): {e}. accessed by admin status:{is_admin}, user:{frontend_user_id}",request, exc_info=True)
        raise HTTPException(status_code=400, detail=HTTP_ERROR_DETAILS["BAD_REQUEST_INVALID_INPUT"])
    except sqlite3.Error as e:
        log_event("error", f"Database error in logs_DB_fetch function (users_and_logs_operations.py): {e}. accessed by admin status:{is_admin}, user:{frontend_user_id}",request, exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_DATABASE"])
    except Exception as e:
        log_event("critical", f"get_event_logs function error (users_and_logs_operations.py): {e}. accessed by admin status:{is_admin}, user:{frontend_user_id}",request, exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_GENERAL_EXCEPTION"])