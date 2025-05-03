from python_standalones.automatic_camera_functions import get_frame_safe
from python_standalones.logger import log_event
from login import authenticate_user
from config.config import FRAME_TIME_INTERVAL,HTTP_ERROR_DETAILS

from fastapi.responses import StreamingResponse
from fastapi import Depends,APIRouter, HTTPException,Request

import face_recognition
import cv2
import asyncio

import time

async def generate_frames():
    """Yields frames asynchronously for live streaming."""
    while True:
        start_time = time.time()
        try:
            frame_local = await asyncio.to_thread(get_frame_safe)
            if frame_local is not None:
                _, buffer = await asyncio.to_thread(cv2.imencode,'.jpg', frame_local)
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                await asyncio.sleep(max(FRAME_TIME_INTERVAL - (time.time() - start_time), 0))  # ~asynced to 20 FPS (0.05) in config.config, possible to adjust after testing
            else:
                yield b'--frame\r\nContent-Type: text/plain\r\n\r\nCamera disconnected, refresh to retry\r\n'
                await asyncio.sleep(max(FRAME_TIME_INTERVAL - (time.time() - start_time), 0))  # Prevents CPU overuse in error case
                continue
        
        except cv2.error as e:
            log_event("critical", f"OpenCV error in generate_frames (livefeeds.py): {e}", exc_info=True)
            yield b'--frame\r\nContent-Type: text/plain\r\n\r\nStream error, retrying...\r\n'
            await asyncio.sleep(1)  # delay for recovery
            continue
        except ValueError as e:
            log_event("critical", f"ValueError in generate_frames (livefeeds.py): {e}", exc_info=True)
            yield b'--frame\r\nContent-Type: text/plain\r\n\r\nInvalid input, retrying...\r\n'
            await asyncio.sleep(1)  # delay for recovery
            continue
        except TypeError as e:
            log_event("critical", f"TypeError in generate_frames (livefeeds.py): {e}", exc_info=True)
            yield b'--frame\r\nContent-Type: text/plain\r\n\r\nType mismatch, retrying...\r\n'
            await asyncio.sleep(1)  # delay for recovery
            continue
        except Exception as e:
            log_event("critical", f"Error in generate_frames (livefeeds.py): {e}", exc_info=True)
            yield b'--frame\r\nContent-Type: text/plain\r\n\r\nStream error, retrying...\r\n'
            await asyncio.sleep(1)  # delay for recovery
            continue

router_livefeed = APIRouter()
@router_livefeed.api_route("/video_feed", methods=["GET", "HEAD"])
async def video_feed(request:Request,current_user: dict = Depends(authenticate_user)):
    """Livestream endpoint for the frontend (Users + Admin)."""
    is_admin, user_id = current_user.get("is_admin"), current_user.get("user_id")
    log_event("info", f"User accessed video_feed function (livefeeds.py), Method: {request.method}, Admin status: {is_admin}, User:{user_id}", request)
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame", headers={"Cache-Control": "no-cache"})
# ------------------------------------------------------------
# ------------------------------------------------------------
async def generate_register_frames():
    """Asynchronously yields frames with face detection for live registration feed."""
    while True:
        start_time = time.time()
        try:
            frame_local = await asyncio.to_thread(get_frame_safe)
            if frame_local is not None:
                # Convert to RGB (face_recognition works with RGB)
                rgb_frame = await asyncio.to_thread(cv2.cvtColor,frame_local,cv2.COLOR_BGR2RGB)
                # Detect faces
                face_locations = await asyncio.to_thread(face_recognition.face_locations,rgb_frame)
                # Draw rectangles on detected faces
                for top, right, bottom, left in face_locations:
                    cv2.rectangle(frame_local, (left, top), (right, bottom), (0, 255, 0), 2)
                # Convert to JPEG format
                _, buffer = await asyncio.to_thread(cv2.imencode,'.jpg', frame_local)
                frame_bytes = buffer.tobytes()
                # Send frame as streaming response
                yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                await asyncio.sleep(max(FRAME_TIME_INTERVAL - (time.time() - start_time), 0))  # ~asynced to 20 FPS (0.05) in config.config, possible to adjust after testing
            else:
                yield (b'--frame\r\nContent-Type: text/plain\r\n\r\nCamera disconnected, refresh to retry\r\n')
                await asyncio.sleep(max(FRAME_TIME_INTERVAL - (time.time() - start_time), 0))  # Prevents CPU overuse in error case
                continue
        
        except cv2.error as e:
            log_event("critical", f"OpenCV error in generate_register_frames (livefeeds.py): {e}", exc_info=True)
            yield b'--frame\r\nContent-Type: text/plain\r\n\r\nStream error, retrying...\r\n'
            await asyncio.sleep(1)  # delay for recovery
            continue
        except ValueError as e:
            log_event("critical", f"ValueError in generate_register_frames (livefeeds.py): {e}", exc_info=True)
            yield b'--frame\r\nContent-Type: text/plain\r\n\r\nInvalid input, retrying...\r\n'
            await asyncio.sleep(1)  # delay for recovery
            continue
        except TypeError as e:
            log_event("critical", f"TypeError in generate_register_frames (livefeeds.py): {e}", exc_info=True)
            yield b'--frame\r\nContent-Type: text/plain\r\n\r\nType mismatch, retrying...\r\n'
            await asyncio.sleep(1)  # delay for recovery
            continue
        except Exception as e:
            log_event("critical", f"Error in generate_register_frames (livefeeds.py): {e}", exc_info=True)
            yield b'--frame\r\nContent-Type: text/plain\r\n\r\nStream error, retrying...\r\n'
            await asyncio.sleep(1)  # delay for recovery
            continue

# special router for face registration live feed
router_register_livefeed = APIRouter()
@router_register_livefeed.get("/register_video_feed")
async def register_video_feed(request:Request,current_user: dict = Depends(authenticate_user)):
    """Asynchronous livestream with face detection (for Admin during registration)."""
    is_admin, user_id = current_user.get("is_admin"), current_user.get("user_id")
    log_event("info", f"User accessed register_video_feed function (livefeeds.py) Admin status: {is_admin}, User:{user_id}", request)
    return StreamingResponse(generate_register_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

    # if not is_admin:
    #     log_event("error", f"Unauthorized access of non admin to register_video_feed function (livefeeds.py) by user {user_id}, admin status: {is_admin}", request)
    #     raise HTTPException(status_code=403, detail=HTTP_ERROR_DETAILS["FORBIDDEN_ADMIN_ONLY"])
 
   # -------- THIS IS INCASE THE HEAD METHOD IS NEEDED (incase the app.api_route wont work) --------
   # @router_livefeed.head("/video_feed") 
   # @router_livefeed.get("/video_feed") 