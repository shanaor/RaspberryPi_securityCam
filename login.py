from config.config import SECRET_KEY, USER_LOG_DB_PATH, TOKEN_EXPIRATION_HOURS
from config.models import UserAuthorization
from python_standalones.logger import log_event

from fastapi import Request, HTTPException, APIRouter, Response
from fastapi.responses import RedirectResponse

from functools import wraps
import jwt
import datetime
import sqlite3
import hashlib


# --------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------
router_login_and_generate_token = APIRouter()
@router_login_and_generate_token.post("/login")
def login_and_generate_token(user: UserAuthorization, request: Request, response: Response):
    """Login and generate a token for the user (Users + Admin)."""
    try:
        with sqlite3.connect(USER_LOG_DB_PATH) as conn:
            cursor = conn.cursor()
            hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
            
            # Check if user is an admin
            cursor.execute("SELECT username, password FROM admin WHERE username = ? AND password = ?", (user.username, hashed_password))
            if cursor.fetchone():
                token = generate_token(user.username, is_admin=True)
                response.set_cookie(key="auth_token", value=token, httponly=True, secure=True, samesite="Lax")
                log_event("info", "User accessed login_and_generate_token function at login.py and got admin permissions",request) 
                return {"message": "Login successful"}
            # Check if user is an active registered user
            cursor.execute("SELECT username, password, is_active FROM registered_users WHERE username = ? AND password = ? AND is_active = 1", (user.username, hashed_password))
            if cursor.fetchone():
                token = generate_token(user.username, is_admin=False)
                response.set_cookie(key="auth_token", value=token, httponly=True, secure=True, samesite="Lax")
                log_event("info", "User accessed login_and_generate_token function at login.py and got user permissions",request) 
                return {"message": "Login successful"}
            log_event("error", "User accessed /login with invalid credentials",request) 
            raise HTTPException(status_code=401, detail="Invalid credentials.")
    except Exception as e:
        log_event("critical", f"login_and_generate_token function error at login.py: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
        
# Token generator module
def generate_token(username: str, is_admin: bool):
    """Generate a JWT token for the user."""
    try:
        expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_EXPIRATION_HOURS)
        payload = {"sub": username, "exp": expiration_time, "admin": is_admin}
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return token
    except Exception as e:
        log_event("critical", f"generate_token function error at login.py error: {e}")
        raise ValueError("Failed to generate token")

# Authentication decorators
def authenticate_user_or_admin(func):
        """Decorator to authenticate users and admins, redirecting on failure."""
        @wraps(func)
        async def wrapper(*args, request: Request, **kwargs):
            try:        
                token = request.cookies.get("auth_token")
                if not token:
                    log_event("error", "Token authentication failed due to no token (authenticate_user_or_admin at login.py)", request)
                    return RedirectResponse(url="/login.html")
                try:
                    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                    # Ensure payload contains either an admin flag or a valid subject
                    if not payload.get("sub"):
                        log_event("error", "Unauthorized access, Not valid user (authenticate_user_or_admin function at login.py)",request)
                        return RedirectResponse(url="/login.html")
                    return await func(*args, request=request, is_authenticated=True, is_admin=payload.get("admin"), **kwargs)
                except jwt.ExpiredSignatureError:
                    log_event("warning", "Token expired (authenticate_user_or_admin at login.py)", request)
                    return RedirectResponse(url="/login.html")
                except jwt.InvalidTokenError:
                    log_event("warning", "Invalid token (authenticate_user_or_admin at login.py)", request)
                    return RedirectResponse(url="/login.html")
            except Exception as e:
                log_event("critical", f"authenticate_user_or_admin function error at login.py error: {e}",request)
                return RedirectResponse(url="/login.html")
        return wrapper

def authenticate_admin(func):
        """Decorator to authenticate admins, redirecting on failure."""
        @wraps(func)
        async def wrapper(*args, request: Request, **kwargs):
            try:
                token = request.cookies.get("auth_token")
                if not token:
                    log_event("error", "Token missing in authenticate_admin",request)
                    return RedirectResponse(url="/login.html")
                try:
                    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                    if not payload.get("admin"):
                        log_event("error", "Admin privileges was tried to be accessed (authenticate_admin function at login.py)",request)
                        return RedirectResponse(url="/login.html")
                    return await func(*args, request=request, is_admin=True, **kwargs)
                except jwt.ExpiredSignatureError:
                    log_event("warning", "Token expired (authenticate_admin at login.py)",request)
                    return RedirectResponse(url="/login.html")
                except jwt.InvalidTokenError:
                    log_event("warning", "Invalid token (authenticate_admin at login.py)",request)
                    return RedirectResponse(url="/login.html")
            except Exception as e:
                log_event("critical", f"authenticate_admin function error at login.py error: {e}",request)
                return RedirectResponse(url="/login.html")
        return wrapper