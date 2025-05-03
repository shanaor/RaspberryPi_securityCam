from config.config import SECRET_KEY, USER_LOG_DB_PATH, TOKEN_EXPIRATION_HOURS,HTTP_ERROR_DETAILS
from config.models import UserAuthorization
from python_standalones.logger import log_event

from fastapi import Request, HTTPException, APIRouter, Response
import sqlite3

import jwt
import datetime
import hashlib
import asyncio

# --------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------
# Token generator module
def generate_token(username: str, is_admin: bool):
    """Generate a JWT token for the user."""
    try:
        expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_EXPIRATION_HOURS)
        payload = {"sub": username, "exp": expiration_time, "admin": is_admin}
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return token
    except Exception as e:
        raise

def check_login_credentials(user):
    "check if login input details are authorized, return dictonary stating the status with boolean"
    try:    
        with sqlite3.connect(USER_LOG_DB_PATH) as conn:
            cursor = conn.cursor()
            hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
            # Check if user is an admin
            cursor.execute("SELECT 1 FROM admin WHERE username = ? AND password = ?", (user.username, hashed_password))
            if cursor.fetchone():
                return {"authenticated": True, "is_admin": True}
            cursor.execute("SELECT 1 FROM registered_users WHERE username = ? AND password = ? AND is_active = 1", (user.username, hashed_password))
            if cursor.fetchone():
                return {"authenticated": True, "is_admin": False}
        return {"authenticated": False}
    except sqlite3.Error as e:
        raise 

router_login_and_generate_token = APIRouter()
@router_login_and_generate_token.post("/login")
async def login_and_generate_token(user: UserAuthorization, request: Request, response: Response):
    """Login and generate a token for the user (Users + Admin).
    used asyncio.to_thread to run the function in a thread pool to avoid blocking and allow concurency.
    (can also change the sqlite3 connection to aiosqlite (wrapper for sqlite) if needed asynced sqilite)."""
    try:
        auth_result = await asyncio.to_thread(check_login_credentials,user)
        if auth_result["authenticated"]:
            token = generate_token(user.username, is_admin=auth_result["is_admin"])
            response.set_cookie(key="auth_token", value=token, httponly=True, secure=True, samesite="Lax")
            permission_level = "admin" if auth_result["is_admin"] else "user"
            log_event("info", f"User: {user.username} accessed login_and_generate_token function, got {permission_level} permissions (login.py)", request) 
            return {"message": "Login successful"}
        log_event("error", f"User: {user.username} accessed /login api with invalid credentials (login.py)", request) 
        raise HTTPException(status_code=401, detail=HTTP_ERROR_DETAILS["INVALID_CREDENTIALS"])
    except HTTPException as e:
        raise
    except ValueError as e:
        log_event("critical", f"ValueError login_and_generate_token error (login.py), tried by {user.username}: {e}", request ,exc_info=True)
        raise HTTPException(status_code=400, detail=HTTP_ERROR_DETAILS["BAD_REQUEST_INVALID_INPUT"])
    except sqlite3.Error as e:
        log_event("critical", f"SQLite error in check_login_credentials function (login.py), tried by {user.username}: {e}", request ,exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_DATABASE"])
    except Exception as e:
        log_event("critical", f"login_and_generate_token function error (login.py), tried by {user.username}: {e}", request ,exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_GENERAL_EXCEPTION"])

# ------------------Authentication decorator-------------------------------------------
def check_if_active(user_id):
    "check if user activated, return result to the upper function to prevent or allow access to the app"
    try:
        with sqlite3.connect(USER_LOG_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_active FROM registered_users WHERE username = ?", (user_id,))
            result = cursor.fetchone()
            return result
    except sqlite3.Error as e:
        raise
                
# Authentication decorator
async def authenticate_user(request: Request):
    """Function to authenticate users and admins, redirecting on failure."""    
    try:        
        token = request.cookies.get("auth_token")
        if not token:
            log_event("error", "Token authentication failed, no token (authenticate_user, login.py)", request)
            raise HTTPException(status_code=401, detail=HTTP_ERROR_DETAILS["AUTH_REQUIRED"])

        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        # Ensure payload contains either an admin flag or a valid subject(user)
        is_admin = payload.get("admin", False)
        user_id = payload.get("sub")
        result = await asyncio.to_thread(check_if_active, user_id)
        # check if user got deactivated while using his token, And edge cases of invalid status (result -> None), like user that was deleted while still having valid token
        if result is None and is_admin == False:
            log_event("error", f"Unautherized access by just deleted user (authenticate_user function ,login.py) tried by {user_id}: {e}", request)
            raise HTTPException(status_code=401, detail=HTTP_ERROR_DETAILS["AUTH_REQUIRED"])
        if result and result[0] == 0:
            log_event("error", f"Unautherized access by just Deactivated (authenticate_user function ,login.py) tried by {user_id}: {e}", request)
            raise HTTPException(status_code=403, detail=HTTP_ERROR_DETAILS["DISABLED_USER"])
        return {"is_admin": is_admin, "user_id": user_id}
    except HTTPException as e:
        raise
    except sqlite3.Error as e:
        log_event("critical", f"SQLite error in check_if_active function (login.py) tried by {user_id}: {e}", request ,exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_DATABASE"])
    except jwt.ExpiredSignatureError as e:
        log_event("warning", f"Token expired in authenticate_user function (login.py) tried by {user_id}: {e}", request ,exc_info=True)
        raise HTTPException(status_code=401, detail=HTTP_ERROR_DETAILS["AUTH_EXPIRED"])
    except jwt.InvalidTokenError as e:
        log_event("warning", f"Invalid token in authenticate_user function (login.py) tried by {user_id}: {e}", request ,exc_info=True)
        raise HTTPException(status_code=401, detail=HTTP_ERROR_DETAILS["AUTH_INVALID_TOKEN"])
    except Exception as e:
        log_event("critical", f"authenticate_user function error (login.py) tried by {user_id}: {e}", request ,exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_VALIDATION"])