import os
import requests
import json
import time
from logger_config import get_logger

logger = get_logger()

def upload_video_to_linkedin(file_path, title, description, access_token, person_urn, organization_urn=None):
    """
    Uploads a video to LinkedIn using the 3-Step Video Upload Process.
    
    Args:
        file_path (str): Path to local video file.
        title (str): Video title.
        description (str): Post text (commentary).
        access_token (str): LinkedIn OAuth2 Access Token.
        person_urn (str): Author URN (e.g., 'urn:li:person:12345') - used if organization_urn is not provided.
        organization_urn (str, optional): Organization URN (e.g., 'urn:li:organization:67890') - for company page posting.
        
    Returns:
        str: URL of the created post (or LinkedIn Activity URN).
    """
    # Use organization URN if provided, otherwise use person URN
    author_urn = organization_urn if organization_urn else person_urn
    
    if not access_token or not author_urn:
        raise ValueError("LinkedIn Access Token and either Person URN or Organization URN are required.")
    
    logger.info(f"Posting as: {'Organization' if organization_urn else 'Personal'} - URN: {author_urn}")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0',
        'LinkedIn-Version': '202405'  # Use latest API version
    }

    try:
        if not os.path.exists(file_path):
             raise FileNotFoundError(f"Video file not found: {file_path}")
        
        file_size = os.path.getsize(file_path)
        
        # Ensure author_urn is properly formatted
        if not author_urn.startswith('urn:li:'):
            # Try to auto-format if it's just a number
            if author_urn.isdigit():
                # Default to organization if we have organization_urn parameter
                if organization_urn:
                    author_urn = f'urn:li:organization:{author_urn}'
                else:
                    author_urn = f'urn:li:person:{author_urn}'
            else:
                logger.warning(f"Author URN may not be properly formatted: {author_urn}")
        
        # --- Step 1: Register Upload ---
        register_url = 'https://api.linkedin.com/v2/assets?action=registerUpload'
        register_data = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-video"],
                "owner": author_urn,
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent"
                    }
                ]
            }
        }
        
        logger.info("Step 1: Registering LinkedIn upload...")
        logger.info(f"Request URL: {register_url}")
        logger.info(f"Request Data: {json.dumps(register_data, indent=2)}")
        logger.info(f"Author URN: {author_urn}")
        
        reg_response = requests.post(register_url, headers=headers, json=register_data)
        
        logger.info(f"Response Status Code: {reg_response.status_code}")
        logger.info(f"Response Headers: {dict(reg_response.headers)}")
        logger.info(f"Response Body: {reg_response.text}")
        
        if reg_response.status_code != 200:
            error_detail = {
                'status_code': reg_response.status_code,
                'response': reg_response.text,
                'person_urn': person_urn
            }
            raise Exception(f"Registration Failed: {reg_response.text}")
            
        reg_json = reg_response.json()
        upload_url = reg_json['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
        asset_urn = reg_json['value']['asset']
        
        logger.info(f"Registered Asset URN: {asset_urn}")
        
        # --- Step 2: Upload Binary ---
        logger.info(f"Step 2: Uploading binary ({file_size} bytes)...")
        with open(file_path, 'rb') as video_file:
            upload_headers = {'Authorization': f'Bearer {access_token}'} # Put specific headers if needed, usually just Authorization
            # LinkedIn upload URL is weird, sometimes needs Content-Type 'application/octet-stream'
            upload_response = requests.put(upload_url, data=video_file, headers={"Authorization": f'Bearer {access_token}', "Content-Type": "application/octet-stream"})
            
            if upload_response.status_code not in [200, 201]:
                 raise Exception(f"Binary Upload Failed: {upload_response.text}")
                 
        logger.info("Binary upload complete.")
        
        # --- Step 3: Check Status (Optional but recommended) ---
        # Note: For many videos, especially smaller ones, processing is instant
        # We'll try to check status but proceed even if this fails
        logger.info("Step 3: Checking video processing status...")
        status_url = f"https://api.linkedin.com/v2/assets/{asset_urn}"
        attempts = 0
        video_ready = False
        
        while attempts < 10:
            try:
                status_resp = requests.get(status_url, headers=headers)
                logger.info(f"Status check response: {status_resp.status_code}")
                
                if status_resp.status_code == 200:
                    status_data = status_resp.json()
                    logger.info(f"Status data: {json.dumps(status_data, indent=2)}")
                    
                    # LinkedIn API response format can vary
                    # Try different possible locations for status
                    status = None
                    
                    if 'recipes' in status_data and len(status_data['recipes']) > 0:
                        status = status_data['recipes'][0].get('status')
                    elif 'recipe' in status_data:
                        status = status_data['recipe'].get('status')
                    elif 'status' in status_data:
                        status = status_data['status']
                    
                    if status == 'AVAILABLE':
                        logger.info("Video processing complete.")
                        video_ready = True
                        break
                    elif status == 'FAILED':
                        raise Exception("LinkedIn Video Processing Failed.")
                    elif status:
                        logger.info(f"Video status: {status}. Waiting...")
                        time.sleep(5)
                        attempts += 1
                    else:
                        # Status field not found, assume it's ready (common for small videos)
                        logger.info("Status field not found in response, assuming video is ready.")
                        video_ready = True
                        break
                else:
                    logger.warning(f"Status check failed with code {status_resp.status_code}, proceeding anyway...")
                    break
            except Exception as e:
                logger.warning(f"Status check error: {e}. Proceeding to post creation anyway...")
                break
        
        if not video_ready and attempts >= 10:
            logger.warning("Video processing status unknown after 10 attempts, proceeding anyway...")
        
        # --- Step 4: Create UGC Post ---
        logger.info("Step 4: Creating UGC Post...")
        post_url = 'https://api.linkedin.com/v2/ugcPosts'
        post_data = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": f"{title}\n\n{description}" if title else description
                    },
                    "media": [
                        {
                            "media": asset_urn,
                            "status": "READY",
                            "title": {
                                "text": title or "New Video"
                            }
                        }
                    ],
                    "shareMediaCategory": "VIDEO"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        logger.info(f"Post URL: {post_url}")
        logger.info(f"Post Data: {json.dumps(post_data, indent=2)}")
        
        create_response = requests.post(post_url, headers=headers, json=post_data)
        
        logger.info(f"Create Post Response Status: {create_response.status_code}")
        logger.info(f"Create Post Response: {create_response.text}")
        
        if create_response.status_code not in [200, 201]:
            raise Exception(f"Create Post Failed: {create_response.text}")
            
        post_id = create_response.json()['id'] # urn:li:share:123 or urn:li:ugcPost:123
        logger.info(f"✅ LinkedIn Post Created Successfully! ID: {post_id}")
        
        # Construct public URL (Approximate, as direct link depends on if it's user or company)
        # Usually https://www.linkedin.com/feed/update/{urn}
        return f"https://www.linkedin.com/feed/update/{post_id}"

    except Exception as e:
        logger.error(f"LinkedIn Upload Error: {e}")
        raise e
