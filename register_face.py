from python_standalones.automatic_camera_functions import get_frame_safe
from python_standalones.logger import log_event
from config.config import SC_DB_PATH
from config.models import FaceName
from login import authenticate_admin

from fastapi import APIRouter, HTTPException,Path
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
def compute_encoding_hash(encoding):
    """Generate a scalar value from a face encoding for fast database lookup by creating first stage filter
    to get canddiates for comparing ."""
    product = np.prod(encoding)
    return float(min(max(product, -1e308), 1e308))  # Multiply all elements together for fast lookup

def save_face_to_db(first_name, last_name, encoding):
    """Store face encoding in SQLite database."""
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
        log_event("critical", f"save_face_to_db function error (register_face.py): {e}")
        raise
# ------------------------------------------------------------
# ------------------------------------------------------------

router_register_face = APIRouter()
@router_register_face.post("/register_face")
@authenticate_admin
async def register_face(user: FaceName):
    """Asynchronously detects a face and registers it, then returns the captured frame to the frontend."""
    try:
        frame_local=await asyncio.to_thread(get_frame_safe)
        if frame_local is None:
            log_event("error", "User accessed register_face function (register_face.py), camera failed",request) # type: ignore
            raise HTTPException(400, "Camera not accessible, please refresh the page.")

        # Convert frame to RGB for face recognition
        rgb_frame = await asyncio.to_thread(cv2.cvtColor,frame_local, cv2.COLOR_BGR2RGB)
        # Detect faces
        face_locations = await asyncio.to_thread(face_recognition.face_locations,rgb_frame)
        face_encodings = await asyncio.to_thread(face_recognition.face_encodings,rgb_frame, face_locations)
        
        if face_encodings: 
            log_event("info", "User accessed register_face function (register_face.py), face detected",request) # type: ignore
            # Process the first face
            location, encoding = face_locations[0], face_encodings[0]
            top, right, bottom, left = location
            cv2.rectangle(frame_local, (left, top), (right, bottom), (0, 255, 0), 2)

            # Convert the frame to Base64
            _, buffer = await asyncio.to_thread(cv2.imencode,'.jpg', frame_local)
            base64_image = base64.b64encode(buffer).decode("utf-8")
            # Save the face encoding in the database (async I/O task)
            await asyncio.to_thread(save_face_to_db, user.first_name, user.last_name, encoding)
            log_event("info", f"User face registered, register_face function: {user.first_name} {user.last_name} (register_face.py)",request) # type: ignore
                
            # Return success response with the image
            return JSONResponse(content={
                "status": "success",
                "message": f"Face registered: {user.first_name} {user.last_name}",
                "image": base64_image
            })
                
        if not face_encodings: #seems redundent because if no face then i can just log and raise error, but its for clarity
            log_event("error", "User accessed register_face function (register_face.py), no face found", request) # type: ignore
        raise HTTPException(400, "No face detected")
    except ValueError as e:
        log_event("error", f"Face detection failed: {e} (register_face.py)")
        raise HTTPException(400, "Invalid image data")
    except sqlite3.Error as e:
        log_event("critical", f"Database error in register_face (register_face.py): {e}")
        raise HTTPException(500, "Database error")
    except Exception as e:
        log_event("critical", f"Unexpected error in register_face (register_face.py): {e}")
        raise HTTPException(500, "Internal server error")
        
router_delete_face = APIRouter()
@router_delete_face.delete("/delete_face/{face_id}")
@authenticate_admin
def delete_face(face_id:int = Path(..., title="Face ID", description="ID must be a positive integer", ge=1)):
    """API endpoint to delete a registered face using its ID (Admin)."""
    try:
        with sqlite3.connect(SC_DB_PATH) as conn:
            cursor = conn.cursor()
            # Check if the ID exists
            cursor.execute('SELECT id FROM registered_faces WHERE id = ?', (face_id,))
            result = cursor.fetchone()

            if not result:
                log_event("error", f"User accessed delete_face function (register_face.py), no face found with ID {face_id}", request) # type: ignore
                raise HTTPException(status_code=404, detail=f"No face found with ID {face_id}")
        # Delete the face record
            cursor.execute('DELETE FROM registered_faces WHERE id = ?', (face_id,))
            conn.commit()
        log_event("warning", f"User accessed delete_face function (register_face.py), face with ID {face_id} deleted", request) # type: ignore
        return {"status": "success", "message": f"Face with ID {face_id} deleted"}
    except sqlite3.Error as e:
        log_event("critical", f"Database error in delete_face (register_face.py): {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        log_event("critical", f"Unexpected error in delete_face (register_face.py): {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
        
router_faces_list = APIRouter()
@router_faces_list.get("/list_faces")
@authenticate_admin
def get_registered_faces():
    """Retrieve a list of all registered faces from the database (Admin)."""
    try:
        with sqlite3.connect(SC_DB_PATH) as conn:
            cursor = conn.cursor()
            # Fetch all registered faces (excluding encodings and encoding_hash)
            cursor.execute('SELECT id, first_name, last_name, created_at FROM registered_faces')
            faces = cursor.fetchall()

        if not faces:
            log_event("info", "User accessed get_registered_faces function (register_face.py), no faces registered", request) # type: ignore
            return {"status": "success", "message": "No faces registered", "faces": []}
        # Convert to list of dictionaries
        face_list = [
            {"id": face[0], "first_name": face[1], "last_name": face[2], "created_at": face[3]}
            for face in faces]
        log_event("info", "User accessed get_registered_faces function (register_face.py)", request) # type: ignore
        return {"status": "success", "faces": face_list}
    except sqlite3.Error as e:
        log_event("critical", f"Database error in get_registered_faces (register_face.py): {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        log_event("critical", f"Unexpected error in get_registered_faces (register_face.py): {e}")
        raise HTTPException(status_code=500, detail="Internal server error")