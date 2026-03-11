import json
import os
import time
import threading
import uuid
from datetime import datetime
from settings_manager import get_user_settings
from logger_config import get_logger

logger = get_logger()

POSTS_DB_FILE = 'scheduled_posts.json'

def load_posts():
    if not os.path.exists(POSTS_DB_FILE):
        return []
    try:
        with open(POSTS_DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_posts(posts):
    with open(POSTS_DB_FILE, 'w') as f:
        json.dump(posts, f, indent=4)

def schedule_post(username, platforms, file_path, caption, schedule_time_str, title="", hashtags=""):
    """
    schedule_time_str: ISO format string or None for immediate.
    """
    posts = load_posts()
    
    post_id = str(int(time.time() * 1000))
    
    new_post = {
        'id': post_id,
        'username': username,
        'platforms': platforms,
        'file_path': file_path,
        'title': title,
        'caption': caption,
        'hashtags': hashtags,
        'schedule_time': schedule_time_str,
        'status': 'scheduled' if schedule_time_str else 'pending',
        'created_at': datetime.now().isoformat()
    }
    
    posts.append(new_post)
    save_posts(posts)
    return post_id

def mock_post_to_platform(platform, api_key, file_path, caption, title="", hashtags="", extra_args=None):
    """
    Simulates posting to a social media platform.
    In a real implementation, this would use libraries like:
    - google-api-python-client (YouTube)
    - tweepy (Twitter)
    - facebook-sdk (FB/Insta)
    """
    if extra_args is None: extra_args = {}
    
    log_file = f"social_media_{platform}.log"
    timestamp = datetime.now().isoformat()
    
    # Simulate API delay related to upload
    time.sleep(2)
    
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] POSTING TO {platform.upper()}\n")
        f.write(f"Key: {api_key[:5]}... (masked)\n")
        if platform == 'youtube' and 'channel_id' in extra_args and extra_args['channel_id']:
            f.write(f"Channel ID: {extra_args['channel_id']}\n")
        f.write(f"File: {file_path}\n")
        f.write(f"Title: {title}\n")
        f.write(f"Caption: {caption}\n")
        f.write(f"Hashtags: {hashtags}\n")
        f.write("-" * 40 + "\n")
        
        if platform == 'youtube':
            # Generate fake video ID
            video_id = str(uuid.uuid4())[:8]
            return f"https://youtu.be/{video_id}"
        elif platform == 'instagram':
             # Generate fake insta ID
            insta_id = str(uuid.uuid4())[:11]
            return f"https://instagram.com/p/{insta_id}"
            
    return "Success"

def process_posts():
    """
    Background task to check for due posts and execute them.
    """
    while True:
        try:
            # 1. Identify posts to process (Read Only)
            posts = load_posts()
            curr_time = datetime.now()
            posts_to_process = []
            
            for post in posts:
                if post['status'] == 'pending':
                    posts_to_process.append(post)
                elif post['status'] == 'scheduled' and post['schedule_time']:
                    try:
                        sched_time = datetime.fromisoformat(post['schedule_time'])
                        if curr_time >= sched_time:
                            posts_to_process.append(post)
                    except ValueError:
                        # Log error but don't crash
                        pass

            # 2. Process each post one by one with fresh loads
            for p_candidate in posts_to_process:
                # Re-load fresh data to ensure we have latest state/lock
                all_posts = load_posts()
                # Find the post by ID
                target_idx = -1
                for i, p in enumerate(all_posts):
                    if p['id'] == p_candidate['id']:
                        target_idx = i
                        break
                
                if target_idx == -1:
                    continue # Post deleted
                    
                target = all_posts[target_idx]
                
                # Double check status is still valid and not picked by another thread
                if target['status'] not in ['scheduled', 'pending']:
                    continue

                if target['status'] == 'scheduled':
                     # Double check time
                     try:
                        s_time = datetime.fromisoformat(target['schedule_time'])
                        if curr_time < s_time:
                            continue
                     except:
                        pass
                
                # MARK PROCESSING - Critical Step
                target['status'] = 'processing'
                save_posts(all_posts) # Commit status change
                
                # Perform Upload
                results = {}
                try:
                    user_settings = get_user_settings(target['username'])
                    for platform in target['platforms']:
                        key_name = f"{platform}_api"
                        api_key = user_settings.get(key_name)
                        
                        try:
                            if platform == 'youtube':
                                from youtube_manager import upload_video_to_youtube
                                video_url = upload_video_to_youtube(
                                    file_path=target['file_path'],
                                    title=target.get('title', 'Untitled Video'),
                                    description=target['caption'],
                                    channel_id=user_settings.get('youtube_channel_id')
                                )
                                results[platform] = video_url
                            elif platform == 'instagram':
                                from instagram_manager import upload_video_to_instagram
                                username = user_settings.get('instagram_username')
                                password = user_settings.get('instagram_password')
                                # Instagram only has a caption field, so combine title and caption
                                full_caption = target['caption']
                                if target.get('title'):
                                    full_caption = f"{target['title']}\n\n{target['caption']}"
                                    
                                video_url = upload_video_to_instagram(
                                    file_path=target['file_path'],
                                    caption=full_caption,
                                    username=username,
                                    password=password
                                )
                                results[platform] = video_url
                            elif platform == 'facebook':
                                from facebook_manager import upload_video_to_facebook
                                page_id = user_settings.get('facebook_page_id')
                                video_url = upload_video_to_facebook(
                                    file_path=target['file_path'],
                                    title=target.get('title', 'Untitled'),
                                    description=target['caption'],
                                    page_id=page_id,
                                    access_token=api_key
                                )
                                results[platform] = video_url
                            elif platform == 'twitter':
                                from twitter_manager import upload_video_to_twitter
                                consumer_key = user_settings.get('twitter_api_key')
                                consumer_secret = user_settings.get('twitter_api_secret')
                                access_token = user_settings.get('twitter_access_token')
                                access_token_secret = user_settings.get('twitter_access_secret')
                                
                                # Twitter also works best with a combined text (limit 280 chars logic is up to user, but we sent it)
                                tweet_text = ""
                                if target.get('title'):
                                    tweet_text += f"{target['title']}\n\n"
                                
                                tweet_text += target['caption'] 
                                
                                if target.get('hashtags'):
                                    tweet_text += f"\n\n{target['hashtags']}"
                                
                                video_url = upload_video_to_twitter(
                                    file_path=target['file_path'],
                                    text=tweet_text,
                                    consumer_key=consumer_key,
                                    consumer_secret=consumer_secret,
                                    access_token=access_token,
                                    access_token_secret=access_token_secret
                                )
                                results[platform] = video_url
                            elif platform == 'linkedin':
                                from linkedin_manager import upload_video_to_linkedin
                                access_token = user_settings.get('linkedin_access_token')
                                person_urn = user_settings.get('linkedin_person_urn')
                                organization_urn = user_settings.get('linkedin_organization_urn')
                                
                                video_url = upload_video_to_linkedin(
                                    file_path=target['file_path'],
                                    title=target.get('title', ''),
                                    description=target['caption'],
                                    access_token=access_token,
                                    person_urn=person_urn,
                                    organization_urn=organization_urn
                                )
                                results[platform] = video_url
                            else:
                                extra_args = {}
                                result = mock_post_to_platform(platform, api_key, target['file_path'], target['caption'], target.get('title', ''), target.get('hashtags', ''), extra_args)
                                results[platform] = result
                        except Exception as e:
                            logger.error(f"Failed to post to {platform}: {e}")
                            results[platform] = f"Failed: {str(e)}"
                            
                except Exception as ex:
                    logger.error(f"Processing error: {ex}")
                    results['error'] = str(ex)

                # MARK COMPLETED
                # Re-load fresh again to avoid overwriting other new posts
                all_posts = load_posts()
                target_idx = -1
                for i, p in enumerate(all_posts):
                    if p['id'] == p_candidate['id']:
                        target_idx = i
                        break
                
                if target_idx != -1:
                     target = all_posts[target_idx]
                     
                     # Determine status
                     any_failure = False
                     all_failures = True
                     if not results:
                         all_failures = True # If loop didn't run?
                     else:
                        for r in results.values():
                             if str(r).startswith("Failed"):
                                 any_failure = True
                             else:
                                 all_failures = False
                     
                     target['results'] = results
                     if all_failures:
                         target['status'] = 'failed'
                     elif any_failure:
                         target['status'] = 'partial'
                     else:
                         target['status'] = 'posted'
                         
                     target['posted_at'] = datetime.now().isoformat()
                     save_posts(all_posts)
            
        except Exception as e:
            print(f"Error in social media processor: {e}")
            logger.error(f"Processor Loop Error: {e}")
            
        time.sleep(10) # Check every 10 seconds

def start_social_media_processor():
    thread = threading.Thread(target=process_posts)
    thread.daemon = True
    thread.start()
def delete_post(post_id, username):
    posts = load_posts()
    new_posts = [p for p in posts if not (p['id'] == post_id and p['username'] == username)]
    if len(posts) != len(new_posts):
        save_posts(new_posts)
        return True
    return False

def get_post(post_id, username):
    posts = load_posts()
    for post in posts:
        if post['id'] == post_id and post['username'] == username:
            return post
    return None

def update_post(post_id, username, data):
    posts = load_posts()
    for post in posts:
        if post['id'] == post_id and post['username'] == username:
            # Update fields
            if 'platforms' in data: post['platforms'] = data['platforms']
            if 'title' in data: post['title'] = data['title']
            if 'caption' in data: post['caption'] = data['caption']
            if 'hashtags' in data: post['hashtags'] = data['hashtags']
            
            # Handle file path update if provided
            if 'file_path' in data and data['file_path']:
                post['file_path'] = data['file_path']
            
            if 'schedule_time' in data: 
                post['schedule_time'] = data['schedule_time']
                # Reset status based on new time
                if post['schedule_time']:
                    post['status'] = 'scheduled'
                else:
                    post['status'] = 'pending'
            elif post['status'] in ['error', 'failed']:
                 # If we didn't change time but are editing a failed post, retry it
                 if post['schedule_time']:
                    post['status'] = 'scheduled'
                 else:
                    post['status'] = 'pending'

            save_posts(posts)
            return True

