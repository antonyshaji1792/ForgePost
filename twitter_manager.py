import os
import tweepy
from logger_config import get_logger

logger = get_logger()

def upload_video_to_twitter(file_path, text, consumer_key, consumer_secret, access_token, access_token_secret):
    """
    Uploads a video to Twitter (X) using Tweepy (v1.1 API for media, v2 for tweet).
    
    Args:
        file_path (str): Local path to video file.
        text (str): Tweet text (caption).
        consumer_key (str): API Key.
        consumer_secret (str): API Secret.
        access_token (str): Access Token.
        access_token_secret (str): Access Token Secret.
        
    Returns:
        str: URL of the posted tweet.
    """
    try:
        if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
            raise ValueError("All Twitter API keys and tokens are required.")
            
        logger.info(f"Starting Twitter upload: {file_path}")
        
        # Authenticate
        auth = tweepy.OAuth1UserHandler(
            consumer_key, consumer_secret,
            access_token, access_token_secret
        )
        api = tweepy.API(auth)
        client = tweepy.Client(
            consumer_key=consumer_key, consumer_secret=consumer_secret,
            access_token=access_token, access_token_secret=access_token_secret
        )
        
        # Verify credentials
        user = api.verify_credentials()
        logger.info(f"Authenticated as Twitter user: {user.screen_name}")
        
        # 1. Upload Video (Use v1.1 API)
        # file_type: 'video/mp4' needs chunked upload
        if not os.path.exists(file_path):
             raise FileNotFoundError(f"File not found: {file_path}")
             
        media = api.media_upload(
            filename=file_path,
            chunked=True, 
            media_category="TWEET_VIDEO"
        )
        
        # Wait for processing if necessary (chunked upload usually handles it, but let's be safe)
        if hasattr(media, 'processing_info'):
            import time
            while media.processing_info['state'] == 'in_progress':
                time.sleep(media.processing_info['check_after_secs'])
                media = api.get_media_upload_status(media.media_id)
        
        logger.info(f"Video uploaded to Twitter media_id: {media.media_id}")
        
        # 2. Post Tweet with Media (Use v2 API for best practices)
        response = client.create_tweet(text=text, media_ids=[media.media_id])
        
        data = response.data
        tweet_id = data['id']
        username = user.screen_name
        
        tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"
        logger.info(f"Tweet posted successfully: {tweet_url}")
        
        return tweet_url
        
    except Exception as e:
        logger.error(f"Error uploading to Twitter: {e}")
        raise e
