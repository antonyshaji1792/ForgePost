import os
import requests
from logger_config import get_logger

logger = get_logger()

def upload_video_to_facebook(file_path, title, description, page_id, access_token):
    """
    Uploads a video to a Facebook Page.
    
    Args:
        file_path (str): Local path to video file.
        title (str): Video title.
        description (str): Video description/caption.
        page_id (str): Facebook Page ID.
        access_token (str): Facebook Page Access Token.
        
    Returns:
        str: URL of the posted video (or success message).
    """
    if not page_id or not access_token:
        raise ValueError("Facebook Page ID and Access Token are required.")
        
    # Use 'me/videos' which automatically resolves to the page/profile context of the token
    # This avoids "global id not allowed" errors if page_id format is confusing (classic vs profile)
    url = f"https://graph-video.facebook.com/v18.0/{page_id}/videos"
    if page_id == 'me':
         url = "https://graph-video.facebook.com/v18.0/me/videos"
    else:
        # Some page IDs require the page access token to specific 'me' context, or the ID is a global ID vs scoped ID.
        # Safest way often is to use the Page Access Token and post to 'me/videos' or '{page_id}/videos'.
        # The error "global id not allowed" suggests the token might be user token trying to post to page, or page token to global ID.
        # If the user provides a Page Access Token, posting to 'me/videos' posts to the page.
        
        # Let's try attempting to use 'me' first if page_id fails?
        # Actually, simpler fixes: just use the endpoint with the ID if proper.
        # But for this specific error: "Global ID not allowed" usually means we are using a User Token to post to a Page ID that isn't scoped correct, or the ID is wrong type.
        # However, for Page Posts, we SHOULD use a Page Access Token. If we have a Page Access Token, 'me' refers to the Page.
        
        pass

    # The user provided a Page ID. The error says that ID is not allowed. 
    # It might be because the token is a Page Token but the ID provided is the numeric ID from the URL which might be correct.
    # But usually with a Page Token, posting to '/me/videos' is the correct way to post AS THE PAGE.
    
    # I will change the default behavior to try using the ID, but if the user wants, we can support 'me'.
    # Actually, to fix this error specifically:
    # If the user provides a Page Access Token, we should just post to `me/videos`.
    # Writing to `{page_id}/videos` should also work, but `me/videos` is safer with Page Tokens.
    
    url = "https://graph-video.facebook.com/v18.0/me/videos"
    
    # Facebook Graph API allows uploading local file via multipart/form-data
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Video file not found: {file_path}")
            
        file_size = os.path.getsize(file_path)
        logger.info(f"Starting Facebook upload: {file_path} ({file_size} bytes)")
        
        # Open file in binary mode
        with open(file_path, 'rb') as f:
            params = {
                'access_token': access_token,
                'title': title,
                'description': description,
            }
            
            files = {
                'source': (os.path.basename(file_path), f, 'video/mp4')
            }
            
            response = requests.post(url, data=params, files=files)
            
            if response.status_code == 200:
                data = response.json()
                video_id = data.get('id')
                logger.info(f"Facebook upload success. Video ID: {video_id}")
                # Construct a direct link
                # If we posted to 'me', we still need the numeric page ID for the public URL if possible.
                # However, the user provided page_id.
                return f"https://www.facebook.com/{page_id}/videos/{video_id}"
            else:
                logger.error(f"Facebook upload failed: {response.text}")
                error_msg = f"Facebook API Error: {response.text}"
                if "No permission to publish" in response.text:
                    error_msg += " (Check if your Page Access Token has 'pages_manage_posts' and 'pages_read_engagement' permissions)"
                raise Exception(error_msg)
                
    except Exception as e:
        logger.error(f"Error uploading to Facebook: {e}")
        raise e
