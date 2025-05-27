from python_standalones.logger import log_event
from config.config import HTTP_ERROR_DETAILS, VIDEO_FOLDER
from login import  authenticate_user

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from typing import List
import os

""" FOR NOW I LEFT THIS MDULE FOR THE FASTAPI AUTOMATIC API ASYNC FUNCTION, TO HADNLE THE CONCURENCY FOR THIS FUNCTIONS. 
THEY ARE SUPPOSED TO BE FAST AND FUNCITONING WELL"""

router_videos_list = APIRouter()
@router_videos_list.get("/videos_list/", response_model=List[str])
def list_videos(request:Request,current_user: dict = Depends(authenticate_user)):
    """List all available video files sorted by modification time (newest first) (Users + Admin). 
    Parses the token to get user information for logging. checks if video folder exists (part of defensive coding method),
    creates it if it doesn't, and raises a 404 error if the folder cannot be accessed or created.
    Returns the list of video filenames sorted by modification time or raises a 404 error if no videos are found."""
    try:
        is_admin = current_user.get("is_admin")
        user_id = current_user.get("user_id")
        
        if not os.path.exists(VIDEO_FOLDER):
            os.makedirs(f"{VIDEO_FOLDER}", exist_ok=True)
            if not os.path.exists(VIDEO_FOLDER):
                log_event("critical", f"User accessed /videos_list, No recordings folder found: {VIDEO_FOLDER} (video_operations.py), accessed by admin status:{is_admin}, user:{user_id}",request) 
                raise HTTPException(status_code=404, detail=HTTP_ERROR_DETAILS["NOT_FOUND_FOLDER"])
        

        # Get all video files in the directory (filtering for .mp4 files and added other formats for flexability if i change the video writer in the future)
        videos = [file for file in os.listdir(VIDEO_FOLDER) if os.path.isfile(os.path.join(VIDEO_FOLDER, file)) and file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]
        # Sort videos by modification time, newest first
        videos.sort(key=lambda file: os.path.getmtime(os.path.join(VIDEO_FOLDER, file)), reverse=True)
        log_event("info", f"Found files in directory: {videos}", request)
        
        if not videos:
            log_event("error", f"User accessed /videos_list, no video was found (video_operations.py), accessed by admin status:{is_admin}, user:{user_id}",request) 
            raise HTTPException(status_code=404, detail=HTTP_ERROR_DETAILS["NOT_FOUND_VIDEOS"])
        log_event("info", f"User accessed /videos_list, listed all videos (video_operations.py), accessed by admin status:{is_admin}, user:{user_id}",request) 
        return videos
    except HTTPException as e:
        raise
    except Exception as e:
        log_event("critical", f"list_videos function error (video_operations.py): {e}. accessed by admin status:{is_admin}, user:{user_id}",request, exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_GENERAL_EXCEPTION"])
    
router_video_download = APIRouter()
@router_video_download.get("/videos/download/{filename}")
def download_video(filename: str,request:Request,current_user: dict = Depends(authenticate_user)):
    """Download a specific video (Users + Admin).
    find the video in the folder using the the frontend list off videos using the video list API
    help prevent wrong file name error."""
    try:
        is_admin = current_user.get("is_admin")
        user_id = current_user.get("user_id")
        
        file_path = os.path.join(VIDEO_FOLDER, filename)
        if not os.path.exists(file_path):
            log_event("error", f"User accessed /videos/download, no video was found (video_operations.py), accessed by admin status:{is_admin}, user:{user_id}",request)
            raise HTTPException(status_code=404, detail=HTTP_ERROR_DETAILS["NOT_FOUND_VIDEO_FILE"])
        log_event("warning", f"User accessed /videos/download, downloaded {filename} (video_operations.py), accessed by admin status:{is_admin}, user:{user_id} ",request)
        return FileResponse(file_path, media_type="video/mp4", filename=filename)
    except HTTPException as e:
        raise
    except Exception as e:
        log_event("critical", f"download_video function error (video_operations.py): {e}. accessed by admin status:{is_admin}, user:{user_id}",request, exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_GENERAL_EXCEPTION"])

router_delete_video = APIRouter()
@router_delete_video.delete("/videos/delete/{filename}")
def delete_video(filename: str,request:Request,current_user: dict = Depends(authenticate_user)):
    """Delete a specific video (Admin only). 
    find the video in the folder using the the frontend list off videos using the video list API
    help prevent wrong file name error."""
    try:
        is_admin = current_user.get("is_admin")
        user_id = current_user.get("user_id")
        
        if not is_admin:
            log_event("error", f"User accessed /videos/delete, not an admin (video_operations.py), accessed by admin status:{is_admin}, user:{user_id}",request)
            raise HTTPException(status_code=403, detail=HTTP_ERROR_DETAILS["FORBIDDEN_ADMIN_ONLY"])
        
        file_path = os.path.join(VIDEO_FOLDER, filename)
        if not os.path.exists(file_path):
            log_event("error", f"User accessed /videos/delete, no video was found (video_operations.py), accessed by admin status:{is_admin}, user:{user_id}",request)
            raise HTTPException(status_code=404, detail=HTTP_ERROR_DETAILS["NOT_FOUND_VIDEO_FILE"])
        os.remove(file_path)
        log_event("warning", f"User accessed /videos/delete and deleted {filename} (video_operations.py). accessed by admin status:{is_admin}, user:{user_id}",request)
        return {"message": f"Video '{filename}' has been deleted."}
    except HTTPException as e:
        raise
    except Exception as e:
        log_event("critical", f"delete_video function error (video_operations.py): {e}. accessed by admin status:{is_admin}, user:{user_id}",request, exc_info=True)
        raise HTTPException(status_code=500, detail=HTTP_ERROR_DETAILS["SERVER_ERROR_GENERAL_EXCEPTION"])