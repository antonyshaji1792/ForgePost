from instagrapi import Client
import os
import time
from logger_config import get_logger

logger = get_logger()

def upload_video_to_instagram(file_path, caption, username, password):
    """
    Uploads a video to Instagram using instagrapi.
    Returns the URL of the posted video.
    """
    try:
        if not username or not password:
            raise ValueError("Instagram username and password are required.")
            
        logger.info(f"Starting Instagram upload for user: {username}")
        
        cl = Client()
        # Create a session file specific to the user
        session_file = f"insta_session_{username}.json"
        
        if os.path.exists(session_file):
            cl.load_settings(session_file)
            try:
                cl.login(username, password)
            except Exception as e:
                logger.warning(f"Session login failed, re-logging in: {e}")
                # If session login fails, try fresh login
                cl = Client()
                cl.login(username, password)
        else:
            cl.login(username, password)
            
        cl.dump_settings(session_file)
        
        logger.info("Logged in to Instagram successfully.")
        
        # Upload video
        # path: Path to clip
        # caption: Media caption
        # thumbnail: Path to thumbnail (optional)
        # usertags: List of users to tag (optional)
        
        media = cl.video_upload(
            file_path,
            caption=caption
        )
        
        # media is a Media object. We need the code to construct the URL.
        # media_code = media.code
        # URL = https://www.instagram.com/p/{code}/
        
        media_code = media.code
        url = f"https://www.instagram.com/p/{media_code}/"
        
        logger.info(f"Instagram upload success: {url}")
        return url
        
    except Exception as e:
        logger.error(f"Instagram upload failed: {e}")
        # Re-raise to be caught by social_media_manager
        raise e
