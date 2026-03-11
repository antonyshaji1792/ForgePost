import os
import pickle
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
from logger_config import get_logger

logger = get_logger()

# Scopes required for uploading

# Scopes required for uploading
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
CLIENT_SECRETS_FILE = "client_secrets.json"
CREDENTIALS_FILE = "credentials.pickle"

def get_authenticated_service():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "rb") as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                raise FileNotFoundError(f"Missing {CLIENT_SECRETS_FILE}. Please download it from Google Cloud Console and place it in the application folder to enable YouTube uploads.")
            
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)
            
        # Save the credentials for the next run
        with open(CREDENTIALS_FILE, "wb") as token:
            pickle.dump(creds, token)

    return googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=creds)

def upload_video_to_youtube(file_path, title,description, category_id="22", privacy_status="public", channel_id=None):
    """
    Uploads a video to YouTube.
    
    Args:
        file_path (str): Path to the video file.
        title (str): Video title.
        description (str): Video description.
        category_id (str): Category ID (default 22 for People & Blogs).
        privacy_status (str): "public", "private", or "unlisted".
        channel_id (str): Optional channel ID to verify targeting (mostly for logging).
    
    Returns:
        str: The YouTube video URL if successful.
    """
    try:
        youtube = get_authenticated_service()

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": [],
                "categoryId": category_id
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            }
        }

        # MediaFileUpload handles the actual file upload
        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

        logger.info(f"Starting upload for video: {file_path}")
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"Uploaded {int(status.progress() * 100)}%")

        logger.info(f"Upload Complete! Video ID: {response['id']}")
        return f"https://youtu.be/{response['id']}"

    except Exception as e:
        logger.error(f"An error occurred during YouTube upload: {e}")
        # Re-raise to be caught by the caller
        raise e
