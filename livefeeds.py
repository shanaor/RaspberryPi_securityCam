from python_standalones.automatic_camera_functions import get_frame_safe
from python_standalones.logger import log_event
from login import authenticate_admin, authenticate_user_or_admin

from fastapi.responses import StreamingResponse
from fastapi import APIRouter

import face_recognition
import cv2
import asyncio

async def generate_frames():
    """Yields frames asynchronously for live streaming."""
    while True:
        try:
            frame_local, ret_local= await asyncio.to_thread(get_frame_safe)
            if frame_local is not None and ret_local:
                _, buffer = await asyncio.to_thread(cv2.imencode,'.jpg', frame_local)
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                await asyncio.sleep(0.033)  # ~30 FPS, possible to adjust after testing

            elif not ret_local:
                yield b'--frame\r\nContent-Type: text/plain\r\n\r\nCamera disconnected, refresh to retry\r\n'
                await asyncio.sleep(0.033)  # Prevents CPU overuse in error case
                continue
        
        except cv2.error as e:
            log_event("critical", f"OpenCV error in generate_frames at livefeeds.py: {e}")
            yield b'--frame\r\nContent-Type: text/plain\r\n\r\nStream error, retrying...\r\n'
            await asyncio.sleep(1)  # delay for recovery
            continue
        except ValueError as e:
            log_event("critical", f"ValueError in generate_frames at livefeeds.py: {e}")
            yield b'--frame\r\nContent-Type: text/plain\r\n\r\nInvalid input, retrying...\r\n'
            await asyncio.sleep(1)  # delay for recovery
            continue
        except TypeError as e:
            log_event("critical", f"TypeError in generate_frames at livefeeds.py: {e}")
            yield b'--frame\r\nContent-Type: text/plain\r\n\r\nType mismatch, retrying...\r\n'
            await asyncio.sleep(1)  # delay for recovery
            continue
        except Exception as e:
            log_event("critical", f"Error in generate_frames at livefeeds.py: {e}")
            yield b'--frame\r\nContent-Type: text/plain\r\n\r\nStream error, retrying...\r\n'
            await asyncio.sleep(1)  # delay for recovery
            continue

router_livefeed = APIRouter()
@router_livefeed.get("/video_feed")
@authenticate_user_or_admin
async def video_feed():
    """Livestream endpoint for the frontend (Users + Admin)."""
    log_event("info", "User accessed video_feed function at livefeeds.py", request) # type: ignore
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")
# ------------------------------------------------------------
# ------------------------------------------------------------
async def generate_register_frames():
    """Asynchronously yields frames with face detection for live registration feed."""
    while True:
        try:
            frame_local, ret_local= await asyncio.to_thread(get_frame_safe)
            if frame_local is not None and ret_local:
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
                await asyncio.sleep(0.1)  # Adjusted for ~10 FPS, tweak after testing
            elif not ret_local:
                yield (b'--frame\r\nContent-Type: text/plain\r\n\r\nCamera disconnected, refresh to retry\r\n')
                await asyncio.sleep(0.1)  # Prevents CPU overuse in error case
                continue
        
        except cv2.error as e:
            log_event("critical", f"OpenCV error in generate_register_frames at livefeeds.py: {e}")
            yield b'--frame\r\nContent-Type: text/plain\r\n\r\nStream error, retrying...\r\n'
            await asyncio.sleep(1)  # delay for recovery
            continue
        except ValueError as e:
            log_event("critical", f"ValueError in generate_register_frames at livefeeds.py: {e}")
            yield b'--frame\r\nContent-Type: text/plain\r\n\r\nInvalid input, retrying...\r\n'
            await asyncio.sleep(1)  # delay for recovery
            continue
        except TypeError as e:
            log_event("critical", f"TypeError in generate_register_frames at livefeeds.py: {e}")
            yield b'--frame\r\nContent-Type: text/plain\r\n\r\nType mismatch, retrying...\r\n'
            await asyncio.sleep(1)  # delay for recovery
            continue
        except Exception as e:
            log_event("critical", f"Error in generate_register_frames at livefeeds.py: {e}")
            yield b'--frame\r\nContent-Type: text/plain\r\n\r\nStream error, retrying...\r\n'
            await asyncio.sleep(1)  # delay for recovery
            continue

# special router for face registration live feed
router_register_livefeed = APIRouter()
@router_register_livefeed.get("/register_video_feed")
@authenticate_admin
async def register_video_feed():
    """Asynchronous livestream with face detection (for Admin during registration)."""
    log_event("info", "User accessed register_video_feed function at livefeeds.py to register a face", request) # type: ignore
    return StreamingResponse(generate_register_frames(), media_type="multipart/x-mixed-replace; boundary=frame")