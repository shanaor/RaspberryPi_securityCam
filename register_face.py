from python_standalones.automatic_camera_functions import get_frame_safe
from python_standalones.logger import log_event
from config.config import HTTP_ERROR_DETAILS, SC_DB_PATH
from config.models import FaceName
from login import authenticate_user

from fastapi import APIRouter, HTTPException,Path,Depends,Request
from fastapi.responses import JSONResponse

import base64
import asyncio

import cv2
import numpy as np
import sqlite3
import face_recognition

""""""""""""""""""""""""""""""""""""
""""""""" ADMIN TERRITORY """""""""
""""""""""""""""""""""""""""""""""""

def compute_encoding_hash(encoding): # The encoding variable here is a local variable using the global value on par with python rules.
    """Generate a scalar value from a face encoding for fast database lookup by creating first stage filter
    to get candidates for comparing"""
    try:
        # Multiply all elements together for fast lookup (---> np.prod(encoding) <---)
        return float(min(max(np.prod(encoding), -1e308), 1e308)) # Clamp the value into the boundries computer allow to avoid overflow and reset of the hash  
    except OverflowError as e:
        raise

def save_face_to_db(first_name, last_name, encoding): # The encoding variable here is a local variable using the global value on par with python rules.
    """Store face encoding in SQLite database. 
    Args: first name, last name, byte code of the face encoding (128 floats), 
          and the encoding hash to use as a fetch key """
    try:
        encoding_hash = compute_encoding_hash(encoding)
        
        with sqlite3.connect(SC_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO registered_faces (first_name, last_name, encoding, encoding_hash) 
                VALUES (?, ?, ?, ?)
            ''', (first_name, last_name, encoding.tobytes(), encoding_hash))
            conn.commit()
    except sqlite3.Error as e:
        raise
# ------------------------------------------------------------
# ------------------------------------------------------------

router_capture_face = APIRouter()
@router_capture_face.get("/capture_face")
async def capture_face(request:Request, current_user: dict = Depends(authenticate_user)):
    """Captures a face from the current frame and returns it to the frontend for preview (Admin)."""
    frame_local = None
    
    try:
        is_admin = current_user.get("is_admin")
        user_id = current_user.get("user_id")
        if not is_admin:
            log_event("error", f"User accessed capture_face function (register_face.py), not an admin. admin status:{is_admin}, user:{user_id}", request)
            raise HTTPException(status_code=403, detail=HTTP_ERROR_DETAILS["FORBIDDEN_ADMIN_ONLY"])
        
        frame_local = await asyncio.wait_for(asyncio.to_thread(get_frame_safe), timeout=5.0) # prevent unresponsiveness of the camera if it gets stuck
        if frame_local is None:
            log_event("error", f"User accessed capture_face function (register_face.py), camera failed. admin status:{is_admin}, user:{user_id}",request)
            raise HTTPException(status_code=400, detail=HTTP_ERROR_DETAILS["BAD_REQUEST_CAMERA_FAIL"])

        # Convert frame to RGB for face recognition
        rgb_frame = await asyncio.wait_for(asyncio.to_thread(cv2.cvtColor,frame_local, cv2.COLOR_BGR2RGB), timeout=2.0)
        # Detect faces
        face_locations = await asyncio.wait_for(asyncio.to_thread(face_recognition.face_locations,rgb_frame), timeout=3.0)
        face_encodings = await asyncio.wait_for(asyncio.to_thread(face_recognition.face_encodings,rgb_frame, face_locations), timeout=3.0)
        
        # Check if any faces were detected
        if face_encodings: 
            log_event("info", "User accessed capture_face function (register_face.py), face detected", request)
            # Process the first face
            location, encoding = face_locations[0], face_encodings[0]
            if not isinstance(encoding, np.ndarray) or encoding.shape[0] != 128:
                log_event("error", "Invalid face encoding shape during registration attempt.", request, exc_info=True)
                raise HTTPException(status_code=422, detail=HTTP_ERROR_DETAILS["BAD_REQUEST_INVALID_INPUT"])
            top, right, bottom, left = location
            await asyncio.wait_for(asyncio.to_thread(cv2.rectangle, frame_local, (left, top), (right, bottom), (0, 255, 0), 2), timeout=2.0)

            # Convert the frame to Base64
            _, buffer = await asyncio.to_thread(cv2.imencode,'.jpg', frame_local)
            base64_image = (await asyncio.to_thread(base64.b64encode, buffer)).decode("utf-8")
            
            # Return success response with the image
            return JSONResponse(content={
                "status": "success",
                "message": "Face detected. If you want to register the Face enter details below.",
                "image": base64_image,
                "encoding": encoding.tolist(),})
        else:
            log_event("error", f"User accessed capture_face function (register_face.py), No face found. admin status:{is_admin}, user:{user_id}", request)
            return JSONResponse(content={"status": "no_face"})

    except HTTPException as e:
        raise   
    except ValueError as e:
        log_event("error", f"Face detection failed at capture_face function (register_face.py): {e}. admin status:{is_admin}, user:{user_id}",request, exc_info=True)
        raise HTTPException(status_code=400, detail=HTTP_ERROR_DETAILS["BAD_REQUEST_INVALID_IMAGE"])
    except asyncio.TimeoutError as e:
        log_event("error", f"Frame capture timed out in capture_face function (register_face.py): {e}. admin status:{is_admin}, user:{user_id}",request, exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_TIMEOUT"].format(error="Face capture failed"))
    except cv2.error as e:
        log_event("error", f"OpenCV error in capture_face function (register_face.py): {e}. admin status:{is_admin}, user:{user_id}",request, exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_OPEN_CV"])
    except Exception as e:
        log_event("critical", f"Unexpected error in capture_face function (register_face.py): {e}. admin status:{is_admin}, user:{user_id}",request, exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_GENERAL_EXCEPTION"])

router_register_face = APIRouter()
@router_register_face.post("/register_face")
async def register_face(user:FaceName, request:Request, current_user: dict = Depends(authenticate_user)):
    """Registers the captured face encoding that was captured by capture_face function and then sent by the frontend with name.
    [FaceName] class is used to validate the input data. and include encoding as a list of floats. (Admin)"""
    try:
        is_admin = current_user.get("is_admin")
        user_id = current_user.get("user_id")
        if not is_admin:
            log_event("error", f"User accessed register_face function (register_face.py), not an admin. admin status:{is_admin}, user:{user_id}", request)
            raise HTTPException(status_code=403, detail=HTTP_ERROR_DETAILS["FORBIDDEN_ADMIN_ONLY"])
            
        # Validate encoding from the request
        encoding = np.array(user.encoding) if user.encoding else None
        if encoding is None:
            log_event("error", f"No face encoding recived from the frontend during registration attempt (register_face function in register_face.py). admin status:{is_admin}, user:{user_id}", request)
            raise HTTPException(status_code=400, detail=HTTP_ERROR_DETAILS["BAD_REQUEST_NO_FACE"])
        if not isinstance(encoding, np.ndarray) or encoding.shape[0] != 128:
            log_event("error", f"Invalid face encoding or shape during registration attempt. (register_face function in register_face.py). admin status:{is_admin}, user:{user_id}", request)
            raise HTTPException(status_code=422, detail=HTTP_ERROR_DETAILS["BAD_REQUEST_INVALID_INPUT"])
        await asyncio.wait_for(asyncio.to_thread(save_face_to_db, user.first_name, user.last_name, encoding), timeout=5.0)
        log_event("info", f"User face registered, register_face function: {user.first_name} {user.last_name} (register_face.py). admin status:{is_admin}, user:{user_id}", request)
        return JSONResponse(content={
            "status": "success",
            "message": f"Face registered: {user.first_name} {user.last_name}",})        
    
    except HTTPException as e:
        raise
    except OverflowError as e:
        log_event("error", f"Overflow error in compute_encoding_hash function (register_face.py): {e}")
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_GENERAL_EXCEPTION"])
    except asyncio.TimeoutError as e:
        log_event("error", f"Registering face timedout in register_face function (register_face.py): {e}. admin status:{is_admin}, user:{user_id}",request, exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_TIMEOUT"].format(error="Registering Face failed"))
    except sqlite3.Error as e:
        log_event("critical", f"Database error in save_face_to_db function (register_face.py): {e}. admin status:{is_admin}, user:{user_id}",request, exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_DATABASE"])
    except Exception as e:
        log_event("critical", f"Unexpected error in register_face function (register_face.py): {e}. admin status:{is_admin}, user:{user_id}",request, exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_GENERAL_EXCEPTION"])
# ----------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------
def delete_DB_check(face_id):
    """ Checks if the face ID exists, if it doesnt then it sends false to the upper function, 
    if exists it deletes the face and returns True to avoid the exception """
    try:
        with sqlite3.connect(SC_DB_PATH) as conn:
            cursor = conn.cursor()
            # Check if the ID exists, if not return the None to the upper function
            cursor.execute('SELECT id FROM registered_faces WHERE id = ?', (face_id,))
            result = cursor.fetchone()
            if not result:
                return False
        # If exists, Delete the face record
            cursor.execute('DELETE FROM registered_faces WHERE id = ?', (face_id,))
            conn.commit()
            return True
    except sqlite3.Error as e:
        raise

router_delete_face = APIRouter()
@router_delete_face.delete("/delete_face/{face_id}")
async def delete_face(request:Request,current_user: dict = Depends(authenticate_user),
                face_id:int = Path(..., title="Face ID", description="ID must be a positive integer", ge=1)):
    """API endpoint to delete a registered face using its ID (Admin)."""
    try:
        is_admin = current_user.get("is_admin")
        user_id = current_user.get("user_id")
        if not is_admin:
            log_event("error", f"User accessed delete_face function (register_face.py), not an admin. admin status:{is_admin} user:{user_id}", request)
            raise HTTPException(status_code=403, detail=HTTP_ERROR_DETAILS["FORBIDDEN_ADMIN_ONLY"])

        result = await asyncio.to_thread(delete_DB_check, face_id)
        if not result:
            log_event("error", f"User accessed delete_face function (register_face.py), no face found with ID {face_id}. admin status:{is_admin} user:{user_id}", request)
            raise HTTPException(status_code=404, detail=HTTP_ERROR_DETAILS["NOT_FOUND_FACE_ID"].format(face_id=face_id))
        log_event("warning", f"User accessed delete_face function (register_face.py), face with ID {face_id} deleted. admin status:{is_admin} user:{user_id}", request)
        return {"status": "success", "message": f"Face with ID {face_id} deleted"}
    except HTTPException as e:
        raise
    except sqlite3.Error as e:
        log_event("critical", f"Database error in delete_DB_check function: {e} (register_face.py). admin status:{is_admin} user:{user_id}",request, exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_DATABASE"])
    except Exception as e:
        log_event("critical", f"Unexpected error in delete_face: {e} (register_face.py). admin status:{is_admin} user:{user_id}",request, exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_GENERAL_EXCEPTION"])
# ----------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------
def face_lists_DB_fetch():
    """ Fetchs the list of registered faces and sends them to the upper function, 
    if list empty returns Empty list[] and skips the If """
    try:
        with sqlite3.connect(SC_DB_PATH) as conn:
            cursor = conn.cursor()
            # Fetch all registered faces (excluding encodings and encoding_hash)
            cursor.execute('SELECT id, first_name, last_name, created_at FROM registered_faces')
            return cursor.fetchall()
    except sqlite3.Error as e:
        raise

router_faces_list = APIRouter()
@router_faces_list.get("/list_faces")
async def get_registered_faces(request:Request,current_user: dict = Depends(authenticate_user)):
    """Retrieve a list of all registered faces from the database."""
    try:
        is_admin = current_user.get("is_admin")
        user_id = current_user.get("user_id")
        if not is_admin:
            log_event("error", f"User accessed get_registered_faces function (register_face.py), not an admin. admin status:{is_admin} user:{user_id}", request)
            raise HTTPException(status_code=403, detail=HTTP_ERROR_DETAILS["FORBIDDEN_ADMIN_ONLY"])

        faces = await asyncio.to_thread(face_lists_DB_fetch)
        if not faces:
            log_event("info", f"User accessed get_registered_faces function (register_face.py), no faces registered. admin status:{is_admin} user:{user_id}", request)
            return {"status": "success", "message": "No faces registered", "faces": []}

        # Convert to list of dictionaries
        face_list = [ {"id": face[0], "first_name": face[1], "last_name": face[2], "created_at": face[3]} for face in faces]
        log_event("info", f"User accessed get_registered_faces function (register_face.py). admin status:{is_admin} user:{user_id}", request)
        return {"status": "success", "faces": face_list}

    except sqlite3.Error as e:
        log_event("critical", f"Database error in face_lists_DB_fetch: {e} (register_face.py). admin status:{is_admin} user:{user_id}",request, exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_DATABASE"])
    except Exception as e:
        log_event("critical", f"Unexpected error in get_registered_faces: {e} (register_face.py). admin status:{is_admin} user:{user_id}",request, exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_GENERAL_EXCEPTION"])
    
# ----------------------POSSIBLE IMPROVEMENTS---------------------- 
# - Add a feature to update the face encoding if the same person is registered again
# - Add a feature to alert the user if the face is already registered
# - Add a feature to infrom the user about already registered name 
# - Add a feature to check if the face is already registered before saving
# - Add a feature to handle multiple faces in a single frame (multi registering process)
# - Add a feature to handle different camera resolutions