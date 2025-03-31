from python_standalones.logger import log_event
from config.config import VIDEO_FOLDER
from login import authenticate_user_or_admin, authenticate_admin

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import List

import os

router_videos_list = APIRouter()
@router_videos_list.get("/videos_list/", response_model=List[str])
@authenticate_user_or_admin
def list_videos():
    """List all available video files (Users + Admin)."""
    try:
        if not os.path.exists(VIDEO_FOLDER):
            os.makedirs(f"{VIDEO_FOLDER}", exist_ok=True)
            if not os.path.exists(VIDEO_FOLDER):
                log_event("critical", "User accessed /videos_list, No recordings folder found (video_operations.py)",request) # type: ignore
                raise HTTPException(status_code=404, detail="No recordings folder found.")
        videos = os.listdir(VIDEO_FOLDER)
        if not videos:
            log_event("error", "User accessed /videos_list, no video was found (video_operations.py)",request) # type: ignore
            raise HTTPException(status_code=404, detail="No videos found.")
        log_event("info", "User accessed /videos_list, listed all videos (video_operations.py)",request) # type: ignore
        return videos
    except Exception as e:
        log_event("critical", f"list_videos function error (video_operations.py): {e}")

router_video_download = APIRouter()
@router_video_download.get("/videos/download/{filename}")
@authenticate_user_or_admin
def download_video(filename: str):
    """Download a specific video (Users + Admin)."""
    try:
        file_path = os.path.join(VIDEO_FOLDER, filename)
        if not os.path.exists(file_path):
            log_event("error", "User accessed /videos/download, no video was found (video_operations.py)",request) # type: ignore
            raise HTTPException(status_code=404, detail="Video not found.")
        log_event("warning", f"User accessed /videos/download, downloaded {filename} (video_operations.py) ",request) # type: ignore
        return FileResponse(file_path, media_type="video/mp4", filename=filename)
    except Exception as e:
        log_event("critical", f"download_video function error (video_operations.py): {e}")
        
router_delete_video = APIRouter()
@router_delete_video.delete("/videos/delete/{filename}")
@authenticate_admin
def delete_video(filename: str):
    """Delete a specific video (Admin)."""
    try:
        file_path = os.path.join(VIDEO_FOLDER, filename)
        if not os.path.exists(file_path):
            log_event("error", "User accessed /videos/delete, no video was found (video_operations.py)",request) # type: ignore
            raise HTTPException(status_code=404, detail="Video not found.")
        os.remove(file_path)
        log_event("warning", f"User accessed /videos/delete and deleted {filename} (video_operations.py)",request) # type: ignore
        return {"message": f"Video '{filename}' has been deleted."}
    except Exception as e:
        log_event("critical", f"delete_video function error (video_operations.py): {e}")