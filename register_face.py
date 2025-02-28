from python_standalones.automatic_camera_functions import get_frame_safe
from python_standalones.logger import log_event
from config.config import SC_DB_PATH
from config.models import UsersName,FaceIdRegex
from login import authenticate_admin

from fastapi import APIRouter, HTTPException
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
    """Generate a unique scalar value from the face encoding."""
    return float(np.prod(encoding))  # Multiply all elements together for fast lookup

def save_face_to_db(first_name, last_name, encoding):
    """Store face encoding in SQLite database."""
    try:
        encoding_hash = compute_encoding_hash(encoding)
        
        conn = sqlite3.connect(SC_DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO registered_faces (first_name, last_name, encoding, encoding_hash) 
            VALUES (?, ?, ?, ?)
        ''', (first_name, last_name, encoding.tobytes(), encoding_hash))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        log_event("critical", f"save_face_to_db function error save at register_face.py: {e}")
# ------------------------------------------------------------
# ------------------------------------------------------------

router_register_face = APIRouter()
@router_register_face.post("/register_face")
@authenticate_admin
async def register_face(user: UsersName):
    """Asynchronously detects a face and registers it, then returns the captured frame to the frontend."""
    try:
        frame_local, ret_local= await asyncio.to_thread(get_frame_safe)
        if not ret_local:
            log_event("error", "User accessed /register_face, camera failed",request) # type: ignore
            return {"status": "error", "message": "Camera not accessible, please refresh the page."}

        # Convert frame to RGB for face recognition
        rgb_frame = await asyncio.to_thread(cv2.cvtColor,frame_local, cv2.COLOR_BGR2RGB)
        # Detect faces
        face_locations = await asyncio.to_thread(face_recognition.face_locations,rgb_frame)
        face_encodings = await asyncio.to_thread(face_recognition.face_encodings,rgb_frame, face_locations)

        if face_encodings:
            log_event("info", "User accessed /register_face face detected",request) # type: ignore
            for location, encoding in zip(face_locations, face_encodings):
                top, right, bottom, left = location
                cv2.rectangle(frame_local, (left, top), (right, bottom), (0, 255, 0), 2)

                # Convert the frame to Base64
                _, buffer = await asyncio.to_thread(cv2.imencode,'.jpg', frame_local)
                base64_image = base64.b64encode(buffer).decode("utf-8")
                # Save the face encoding in the database (async I/O task)
                await asyncio.to_thread(save_face_to_db, user.first_name, user.last_name, encoding)
                log_event("info", f"User registered: {user.first_name} {user.last_name}",request) # type: ignore
                
                # Return success response with the image
                return JSONResponse(content={
                    "status": "success",
                    "message": f"Face registered: {user.first_name} {user.last_name}",
                    "image": base64_image
                })
        log_event("error", "User accessed /register_face, no face found",request) # type: ignore
        return {"status": "failed", "message": "No face detected"}
    except Exception as e:
        log_event("critical", f"register_face function error at register_face.py: {e}")
        
router_delete_face = APIRouter()
@router_delete_face.delete("/delete_face/{face_id}")
@authenticate_admin
def delete_face(face_id: FaceIdRegex ):
    """API endpoint to delete a registered face using its ID (Admin)."""
    try:
        conn = sqlite3.connect(SC_DB_PATH)
        cursor = conn.cursor()
        # Check if the ID exists
        cursor.execute('SELECT id FROM registered_faces WHERE id = ?', (face_id.face_id,))
        result = cursor.fetchone()

        if not result:
            conn.close()
            log_event("error", f"User accessed /delete_face No face found with ID {face_id.face_id}",request) # type: ignore
            raise HTTPException(status_code=404, detail=f"No face found with ID {face_id.face_id}")
        # Delete the face record
        cursor.execute('DELETE FROM registered_faces WHERE id = ?', (face_id.face_id,))
        conn.commit()
        conn.close()
        log_event("warning", f"User accessed /delete_face Face with ID {face_id.face_id} deleted",request) # type: ignore
        return {"status": "success", "message": f"Face with ID {face_id.face_id} deleted"}
    except Exception as e:
        log_event("critical", f"delete_face function error at register_face.py: {e}")
        
router_faces_list = APIRouter()
@router_faces_list.get("/list_faces")
@authenticate_admin
def get_registered_faces():
    """Retrieve a list of all registered faces from the database (Admin)."""
    try:
        conn = sqlite3.connect(SC_DB_PATH)
        cursor = conn.cursor()
        # Fetch all registered faces (excluding encodings and encoding_hash)
        cursor.execute('SELECT id, first_name, last_name, created_at FROM registered_faces')
        faces = cursor.fetchall()
        conn.close()

        if not faces:
            log_event("error", "User accessed /list_faces, No faces registered",request) # type: ignore
            return {"status": "success", "message": "No faces registered"}
        # Convert to list of dictionaries
        face_list = [
            {"id": face[0], "first_name": face[1], "last_name": face[2], "created_at": face[3]}
            for face in faces]
        log_event("info", "User accessed /list_faces",request) # type: ignore
        return {"status": "success", "faces": face_list}
    except Exception as e:
        log_event("critical", f"get_registered_faces function error at register_face.py: {e}")