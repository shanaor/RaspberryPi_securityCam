from config.config import SECRET_KEY, USER_LOG_DB_PATH, TOKEN_EXPIRATION_HOURS,HTTP_ERROR_DETAILS
from config.models import UserAuthorization
from python_standalones.logger import log_event

from fastapi import Request, HTTPException, APIRouter, Response

import jwt
import datetime
import sqlite3
import hashlib


# --------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------
router_login_and_generate_token = APIRouter()
@router_login_and_generate_token.post("/login")
def login_and_generate_token(user: UserAuthorization, request: Request, response: Response):
    """Login and generate a token for the user (Users + Admin). not asynced because this is a home system. low amount of users. 
    if needed to change to async, change the sqlite3 connection to aiosqlite (wrapper for sqlite) or use asyncio run()/asyncio.to_thread to run the function in a thread pool."""
    try:
        with sqlite3.connect(USER_LOG_DB_PATH) as conn:
            cursor = conn.cursor()
            hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
    
            # Check if user is an admin
            cursor.execute("SELECT username, password FROM admin WHERE username = ? AND password = ?", (user.username, hashed_password))
            if cursor.fetchone():
                token = generate_token(user.username, is_admin=True)
                response.set_cookie(key="auth_token", value=token, httponly=True, secure=False, samesite="Lax")
                log_event("info", "User accessed login_and_generate_token function, got admin permissions (login.py)", request) 
                return {"message": "Login successful"}
            # Check if user is an active registered user
            cursor.execute("SELECT username, password, is_active FROM registered_users WHERE username = ? AND password = ? AND is_active = 1", (user.username, hashed_password))
            if cursor.fetchone():
                token = generate_token(user.username, is_admin=False)
                response.set_cookie(key="auth_token", value=token, httponly=True, secure=False, samesite="Lax")
                log_event("info", "User accessed login_and_generate_token function, got user permissions (login.py)", request) 
                return {"message": "Login successful"}
            log_event("error", "User accessed /login api with invalid credentials (login.py)", request) 
            raise HTTPException(status_code=401, detail=HTTP_ERROR_DETAILS["INVALID_CREDENTIALS"])
    except HTTPException as e:
        log_event("error", f"HTTPException in login_and_generate_token function (login.py): {e}", request)
        raise
    except sqlite3.Error as e:
        log_event("critical", f"SQLite error in login_and_generate_token function (login.py): {e}")
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_DATABASE"])
    except Exception as e:
        log_event("critical", f"login_and_generate_token function error (login.py): {e}")
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_GENERAL_EXCEPTION"])

# Token generator module
def generate_token(username: str, is_admin: bool):
    """Generate a JWT token for the user."""
    try:
        expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_EXPIRATION_HOURS)
        payload = {"sub": username, "exp": expiration_time, "admin": is_admin}
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return token
    except Exception as e:
        log_event("critical", f"generate_token function error (login.py): {e}")
        raise ValueError(f"Failed to generate token generate_token function (login.py): {e}")

# Authentication decorators
async def authenticate_user(request: Request):
    """Function to authenticate users and admins, redirecting on failure."""    
    try:        
        token = request.cookies.get("auth_token")
        if not token:
            log_event("error", "Token authentication failed, no token (authenticate_user_or_admin, login.py)", request)
            raise HTTPException(status_code=401, detail=HTTP_ERROR_DETAILS["AUTH_REQUIRED"])

        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        # Ensure payload contains either an admin flag or a valid subject(user)
        is_admin = payload.get("admin", False)
        user_id = payload.get("sub")
        return {"is_admin": is_admin, "user_id": user_id}
    except HTTPException as e:
        log_event("error", f"HTTPException in authenticate_user function (login.py): {e}", request)
        raise
    except jwt.ExpiredSignatureError as e:
            log_event("warning", f"Token expired in authenticate_user_or_admin function (login.py): {e}", request)
            raise HTTPException(status_code=401, detail=HTTP_ERROR_DETAILS["AUTH_EXPIRED"])
    except jwt.InvalidTokenError as e:
            log_event("warning", f"Invalid token in authenticate_user_or_admin function (login.py): {e}", request)
            raise HTTPException(status_code=401, detail=HTTP_ERROR_DETAILS["AUTH_INVALID_TOKEN"])
    except Exception as e:
        log_event("critical", f"authenticate_user_or_admin function error (login.py): {e}",request)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_VALIDATION"])