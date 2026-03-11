from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
import os
import secrets
import json
import threading
import asyncio
import time
import urllib.request
import urllib.error
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips
import uuid
from social_media_manager import schedule_post, get_post, update_post, delete_post, start_social_media_processor, load_posts
from settings_manager import get_user_settings, update_user_settings
from auth_manager import register_user, authenticate_user, init_db
from merge_video_audio import merge_video_audio
from combine_video import combine_videos
from trim_video import trim_video
from trim_audio import trim_audio
from text_to_speech import text_to_speech
from logger_config import get_logger

logger = get_logger()

app = Flask(__name__)
app.secret_key = 'super-secret-key-forgepost'

BASE_UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
BASE_OUTPUT_FOLDER = os.path.join(os.getcwd(), 'outputs')
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'mp3', 'wav', 'aac'}

app.config['UPLOAD_FOLDER'] = BASE_UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = BASE_OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

# Ensure base directories exist
os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(BASE_OUTPUT_FOLDER, exist_ok=True)
init_db()

# In-memory job store
# In-memory job store - replaced with persistent file store
JOBS_FILE = 'jobs.json'
job_lock = threading.Lock()

def load_jobs():
    if not os.path.exists(JOBS_FILE):
        return {}
    try:
        with open(JOBS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_jobs(jobs_data):
    with job_lock:
        with open(JOBS_FILE, 'w') as f:
            json.dump(jobs_data, f, indent=4)

def get_job(job_id):
    jobs = load_jobs()
    return jobs.get(job_id)

def update_job(job_id, data):
    with job_lock:
        # We need to read-modify-write safely
        jobs = load_jobs()
        if job_id not in jobs:
            jobs[job_id] = {}
        jobs[job_id].update(data)
        
        # Save directly (save_jobs already has lock, but re-entrant lock is needed or avoid double lock)
        # recursive lock or just code duplication.
        # simpler:
        with open(JOBS_FILE, 'w') as f:
            json.dump(jobs, f, indent=4)

# Initialize jobs file if needed
if not os.path.exists(JOBS_FILE):
    save_jobs({})

jobs = load_jobs() # For compatibility if accessed directly, but better to use helpers


def get_user_folders():
    if 'user' in session:
        user_upload = os.path.join(BASE_UPLOAD_FOLDER, session['user'])
        user_output = os.path.join(BASE_OUTPUT_FOLDER, session['user'])
    else:
        # Guest user
        user_upload = os.path.join(BASE_UPLOAD_FOLDER, 'temp')
        user_output = os.path.join(BASE_OUTPUT_FOLDER, 'temp')
        
    os.makedirs(user_upload, exist_ok=True)
    os.makedirs(user_output, exist_ok=True)
    return user_upload, user_output

def cleanup_temp_files():
    """Background task to clean up temp files older than 15 minutes"""
    while True:
        try:
            temp_dirs = [
                os.path.join(BASE_UPLOAD_FOLDER, 'temp'),
                os.path.join(BASE_OUTPUT_FOLDER, 'temp')
            ]
            
            cutoff_time = time.time() - (15 * 60) # 15 minutes ago
            
            for folder in temp_dirs:
                if os.path.exists(folder):
                    for filename in os.listdir(folder):
                        file_path = os.path.join(folder, filename)
                        if os.path.isfile(file_path):
                            file_mtime = os.path.getmtime(file_path)
                            if file_mtime < cutoff_time:
                                try:
                                    os.remove(file_path)
                                    print(f"Cleaned up temp file: {filename}")
                                except Exception as e:
                                    print(f"Error deleting {filename}: {e}")
        except Exception as e:
            print(f"Error in cleanup task: {e}")
            
        time.sleep(60) # Run every minute

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if authenticate_user(username, password):
            session['user'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    success, msg = register_user(username, password)
    if success:
        return render_template('login.html', message="Registration successful! Please login.")
    else:
        return render_template('login.html', error=msg)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    username = session['user']
    
    if request.method == 'POST':
        new_settings = {
            'youtube_api': request.form.get('youtube_api'),
            'youtube_channel_id': request.form.get('youtube_channel_id'),
            'instagram_username': request.form.get('instagram_username'),
            'instagram_password': request.form.get('instagram_password'),
            'facebook_page_id': request.form.get('facebook_page_id'),
            'facebook_api': request.form.get('facebook_api'),
            'twitter_api_key': request.form.get('twitter_api_key'),
            'twitter_api_secret': request.form.get('twitter_api_secret'),
            'twitter_access_token': request.form.get('twitter_access_token'),
            'twitter_access_secret': request.form.get('twitter_access_secret'),
            'linkedin_access_token': request.form.get('linkedin_access_token'),
            'linkedin_person_urn': request.form.get('linkedin_person_urn'),
            'linkedin_organization_urn': request.form.get('linkedin_organization_urn')
        }
        
        # LLM Providers
        providers = ['openrouter', 'openai', 'anthropic', 'google', 'mistral', 'cohere', 'huggingface', 'groq', 'perplexity', 'together', 'deepseek']
        for p in providers:
            new_settings[f"{p}_api"] = request.form.get(f"{p}_api")
            new_settings[f"{p}_model"] = request.form.get(f"{p}_model")
            new_settings[f"{p}_active"] = 'on' if request.form.get(f"{p}_active") else 'off'
            
        update_user_settings(username, new_settings)
        # Reload settings to ensure we show what was saved (including previous values if any were missed, though update merges)
        # Actually update_user_settings merges into existing file, but 'new_settings' only has what we just submitted.
        # We should reload the full settings to pass back to template.
        updated_settings = get_user_settings(username)
        return render_template('settings.html', user=username, settings=updated_settings, message="Settings saved successfully!")
    
    # GET request
    user_settings = get_user_settings(username)
    return render_template('settings.html', user=username, settings=user_settings)

@app.route('/social')
def social_dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    username = session['user']
    _, user_output = get_user_folders()
    
    # List files for selection
    files = []
    if os.path.exists(user_output):
        files = [f for f in os.listdir(user_output) if os.path.isfile(os.path.join(user_output, f)) and not f.startswith('.')]
        # Sort by newest
        files.sort(key=lambda x: os.path.getmtime(os.path.join(user_output, x)), reverse=True)
        
    # Get user's post history
    all_posts = load_posts()
    # Filter for this user
    user_posts = [p for p in all_posts if p['username'] == username]
    # Sort by time, newest first
    user_posts.sort(key=lambda x: x['created_at'], reverse=True)
    
    return render_template('social.html', user=username, files=files, posts=user_posts)

@app.route('/history')
def post_history():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    username = session['user']
    
    # Get user's post history
    all_posts = load_posts()
    # Filter for this user
    user_posts = [p for p in all_posts if p['username'] == username]
    # Sort by time, newest first
    user_posts.sort(key=lambda x: x['created_at'], reverse=True)
    
    return render_template('history.html', user=username, posts=user_posts)

@app.route('/logs')
def view_logs():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    log_content = ""
    if os.path.exists("app.log"):
        with open("app.log", "r", encoding="utf-8") as f:
            log_content = f.read()
            
    return render_template('logs.html', user=session['user'], logs=log_content)

@app.route('/api/schedule_post', methods=['POST'])
def handle_schedule_post():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    username = session['user']
    _, user_output = get_user_folders()
    
    filename = request.form.get('filename')
    platforms = request.form.getlist('platforms')
    caption = request.form.get('caption')
    title = request.form.get('title')
    hashtags = request.form.get('hashtags')
    schedule_time = request.form.get('schedule_time') # e.g., "2023-12-06T15:30"
    
    # Check for file upload
    if 'file_upload' in request.files:
        file = request.files['file_upload']
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(user_output, filename))
    
    if not filename or not platforms:
        return "Missing filename or platforms", 400
        
    file_path = os.path.join(user_output, filename)
    if not os.path.exists(file_path):
        return "File not found", 404
        
    # If schedule_time is empty, pass None for immediate posting (handled by manager as 'pending')
    if not schedule_time:
        schedule_time = None
        
    # Process hashtags
    if hashtags:
        tags = [t.strip() for t in hashtags.split(',') if t.strip()]
        # Ensure # prefix
        tags = ['#' + t if not t.startswith('#') else t for t in tags]
        hashtags = ' '.join(tags)
        
    schedule_post(username, platforms, file_path, caption, schedule_time, title, hashtags)
    
    return redirect(url_for('post_history'))

@app.route('/api/delete_post/<post_id>', methods=['POST'])
def delete_social_post(post_id):
    if 'user' not in session:
        return redirect(url_for('login'))
        
    username = session['user']
    if delete_post(post_id, username):
        return redirect(url_for('post_history'))
    else:
        return "Failed to delete post", 400

@app.route('/edit_post/<post_id>')
def edit_post(post_id):
    if 'user' not in session:
        return redirect(url_for('login'))
        
    username = session['user']
    post = get_post(post_id, username)
    if not post:
        return "Post not found or unauthorized", 404
    
    # Check if we can edit
    if post['status'] not in ['scheduled', 'pending', 'failed', 'error']:
         # Maybe allow viewing but not editing? Or just redirect.
         # User asked to edit scheduled/pending/failed.
         pass # Assume we let them try, if it's 'posted' maybe we shouldn't.
         
    if post['status'] == 'posted':
         return "Cannot edit posted content. Please create a new post.", 403

    _, user_output = get_user_folders()
    # List files for potential re-selection (optional, but good to have)
    files = []
    if os.path.exists(user_output):
        files = [f for f in os.listdir(user_output) if os.path.isfile(os.path.join(user_output, f)) and not f.startswith('.')]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(user_output, x)), reverse=True)

    return render_template('edit_post.html', user=username, post=post, files=files)

@app.route('/api/update_post/<post_id>', methods=['POST'])
def handle_update_post(post_id):
    if 'user' not in session:
        return redirect(url_for('login'))
        
    username = session['user']
    
    # Collect form data
    platforms = request.form.getlist('platforms')
    caption = request.form.get('caption')
    title = request.form.get('title')
    hashtags = request.form.get('hashtags')
    schedule_time = request.form.get('schedule_time')
    filename = request.form.get('filename') # If user changed file
    
    # Process hashtags
    if hashtags:
        tags = [t.strip() for t in hashtags.split(',') if t.strip()]
        tags = ['#' + t if not t.startswith('#') else t for t in tags]
        hashtags = ' '.join(tags)
    
    data = {
        'platforms': platforms,
        'caption': caption,
        'title': title,
        'hashtags': hashtags,
        'schedule_time': schedule_time if schedule_time else None
    }
    
    # Handle filename change if present
    if filename:
        _, user_output = get_user_folders()
        file_path = os.path.join(user_output, filename)
        if os.path.exists(file_path):
             data['file_path'] = file_path
    
    if update_post(post_id, username, data):
        return redirect(url_for('post_history'))
    else:
        return "Failed to update post", 400


def call_llm(provider, api_key, model, prompt):
    endpoints = {
        'openrouter': 'https://openrouter.ai/api/v1/chat/completions',
        'openai': 'https://api.openai.com/v1/chat/completions',
        'groq': 'https://api.groq.com/openai/v1/chat/completions',
        'deepseek': 'https://api.deepseek.com/chat/completions',
        'mistral': 'https://api.mistral.ai/v1/chat/completions',
        'together': 'https://api.together.xyz/v1/chat/completions'
    }
    
    url = endpoints.get(provider)
    if not url:
         # Fallback or specific handling could be added here
         raise Exception(f"Provider {provider} not supported for auto-generation yet")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    if provider == 'openrouter':
        headers['HTTP-Referer'] = 'http://localhost:5000'
        headers['X-Title'] = 'ForgePost'

    payload = {
        "model": model if model else "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req) as response:
            try:
                response_data = json.loads(response.read().decode('utf-8'))
            except:
                # sometimes read can be called only once
                response_data = json.loads(response.read())

            content = response_data['choices'][0]['message']['content']
            
            # Parse responses
            lines = [l.strip() for l in content.split('\n') if l.strip()]
            clean_lines = []
            for l in lines:
                # Remove numbering and quotes
                if len(l) > 2 and l[0].isdigit() and l[1] in ['.', ')']:
                    l = l[2:].strip()
                elif l.startswith('- '):
                    l = l[2:].strip()
                if l.startswith('"') and l.endswith('"'):
                    l = l[1:-1].strip()
                clean_lines.append(l)
                
            return clean_lines[:3] 
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"LLM API Error: {error_body}")
        raise Exception(f"API Error: {e.reason}")
    except Exception as e:
        print(f"LLM Call Error: {e}")
        raise e

@app.route('/api/generate_titles', methods=['POST'])
def generate_titles_endpoint():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    original_title = data.get('title')
    
    if not original_title:
        return jsonify({'error': 'Missing title'}), 400
        
    username = session['user']
    settings = get_user_settings(username)
    
    # Find active provider
    provider = None
    api_key = None
    model = None
    
    providers = ['openrouter', 'openai', 'anthropic', 'google', 'mistral', 'cohere', 'huggingface', 'groq', 'perplexity', 'together', 'deepseek']
    
    for p in providers:
        if settings.get(f'{p}_active') == 'on':
            key = settings.get(f'{p}_api')
            if key:
                provider = p
                api_key = key
                model = settings.get(f'{p}_model')
                break
    
    if not provider:
        return jsonify({'error': 'No active LLM provider found in Settings. Please configure one in Settings.'}), 400
        
    prompt = f"Rewrite the following social media post title into 3 catchy, engaging variations. Return ONLY the 3 titles, one per line. Do not number them. Title: {original_title}"
    
    try:
        titles = call_llm(provider, api_key, model, prompt)
        return jsonify({'titles': titles})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_description', methods=['POST'])
def generate_description_endpoint():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    title = data.get('title', '')
    description = data.get('description', '')
    
    if not title and not description:
        return jsonify({'error': 'Missing title or description'}), 400
        
    username = session['user']
    settings = get_user_settings(username)
    
    # Find active provider
    provider = None
    api_key = None
    model = None
    
    providers = ['openrouter', 'openai', 'anthropic', 'google', 'mistral', 'cohere', 'huggingface', 'groq', 'perplexity', 'together', 'deepseek']
    
    for p in providers:
        if settings.get(f'{p}_active') == 'on':
            key = settings.get(f'{p}_api')
            if key:
                provider = p
                api_key = key
                model = settings.get(f'{p}_model')
                break
    
    if not provider:
        return jsonify({'error': 'No active LLM provider found.'}), 400
        
    if description:
        prompt = f"Rewrite and improve the following social media post description to be more engaging and professionally written. Provide 3 slightly different variations (e.g. one short and punchy, one detailed). Return ONLY the 3 descriptions separated by a standard newline, do not number them, do not use quotes. Description: {description}. Context Title: {title}"
    else:
        # Generate based on title
        prompt = f"Write 3 engaging social media post descriptions for a video titled '{title}'. Provide 3 variations (e.g. one short, one longer with hashtags, one question-based). Return ONLY the 3 descriptions, separated by a standard newline, do not number them."
    
    try:
        # Reuse call_llm but might need to handle newlines differently effectively since descriptions can be multiline?
        # call_llm splits by \n. Descriptions themselves might have newlines.
        # This calls for a slightly different parsing or just accepting that call_llm returns a list of lines. 
        # If call_llm splits every line, and a description has multiple lines, we get fragmented descriptions.
        # We should modify call_llm or just implement a custom call here?
        # Actually call_llm logic: `lines = [l.strip() for l in content.split('\n') if l.strip()]`
        # If I ask for descriptions separated by "|||", I can parse better.
        
        # Let's override the prompt to ask for specific separator
        prompt += " Separate each variation with '|||'."
        
        # We'll use a custom request here or modify call_llm to support raw return. 
        # Let's just do a specific implementation here to avoid breaking call_llm for titles.
        
        # ... Or just copy-paste the request logic since call_llm is hardcoded to return clean_lines[:3]
        
        endpoints = {
            'openrouter': 'https://openrouter.ai/api/v1/chat/completions',
            'openai': 'https://api.openai.com/v1/chat/completions',
            'groq': 'https://api.groq.com/openai/v1/chat/completions',
            'deepseek': 'https://api.deepseek.com/chat/completions',
            'mistral': 'https://api.mistral.ai/v1/chat/completions',
            'together': 'https://api.together.xyz/v1/chat/completions'
        }
        
        url = endpoints.get(provider)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        if provider == 'openrouter':
            headers['HTTP-Referer'] = 'http://localhost:5000'
            headers['X-Title'] = 'ForgePost'
    
        payload = {
            "model": model if model else "openai/gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}]
        }
        
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req) as response:
            try:
                response_data = json.loads(response.read().decode('utf-8'))
            except:
                response_data = json.loads(response.read())
            
            content = response_data['choices'][0]['message']['content']
            
            # Split by separator
            if '|||' in content:
                descriptions = [d.strip() for d in content.split('|||') if d.strip()]
            else:
                # Fallback if AI didn't listen
                descriptions = [content]
                
            return jsonify({'descriptions': descriptions})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/')
def index():
    user = session.get('user')
    return render_template('index.html', user=user)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    user_upload, _ = get_user_folders()
    return send_from_directory(user_upload, filename)

@app.route('/outputs/<filename>')
def output_file(filename):
    _, user_output = get_user_folders()
    return send_from_directory(user_output, filename)

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    filename = secure_filename(filename) 
    _, user_output = get_user_folders()
    file_path = os.path.join(user_output, filename)
    
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/delete_bulk', methods=['POST'])
def delete_bulk():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.json
    filenames = data.get('filenames', [])
    
    if not filenames:
        return jsonify({'error': 'No files specified'}), 400
        
    _, user_output = get_user_folders()
    deleted_count = 0
    errors = []
    
    for filename in filenames:
        filename = secure_filename(filename)
        file_path = os.path.join(user_output, filename)
        
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                deleted_count += 1
            except Exception as e:
                errors.append(f"Failed to delete {filename}: {str(e)}")
        else:
            errors.append(f"File not found: {filename}")
            
    return jsonify({
        'success': True, 
        'deleted_count': deleted_count,
        'errors': errors
    })

@app.route('/gallery')
def gallery():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    _, user_output = get_user_folders()
    
    files = os.listdir(user_output)
    # Filter only files
    files = [f for f in files if os.path.isfile(os.path.join(user_output, f))]
    
    # Sort by modification time, newest first
    files.sort(key=lambda x: os.path.getmtime(os.path.join(user_output, x)), reverse=True)
    
    categories = {
        'Merge': [],
        'Combine': [],
        'Trim Video': [],
        'Trim Audio': [],
        'Text to Speech': [],
        'Other': []
    }
    
    for f in files:
        if f.startswith('merge_'):
            categories['Merge'].append(f)
        elif f.startswith('combine_'):
            categories['Combine'].append(f)
        elif f.startswith('trim_') and not f.startswith('trim_audio_'):
            categories['Trim Video'].append(f)
        elif f.startswith('trim_audio_'):
            categories['Trim Audio'].append(f)
        elif f.startswith('tts_'):
            categories['Text to Speech'].append(f)
        else:
            categories['Other'].append(f)
            
    return render_template('gallery.html', categories=categories, has_files=bool(files), user=session['user'])

@app.route('/status/<job_id>')
def job_status(job_id):
    job = get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(job)

def run_merge_task(job_id, video_path, audio_path, output_folder):
    with app.app_context():
        try:
            update_job(job_id, {'status': 'processing'})
            output_filename = f"merge_{job_id}.mp4"
            output_path = os.path.join(output_folder, output_filename)
            
            success = merge_video_audio(video_path, audio_path, output_path)
            
            if success:
                update_job(job_id, {'status': 'completed', 'output_url': f"/outputs/{output_filename}"})
            else:
                update_job(job_id, {'status': 'error', 'message': 'Merging failed'})
        except Exception as e:
            update_job(job_id, {'status': 'error', 'message': str(e)})

def run_combine_task(job_id, video1_path, video2_path, output_folder):
    with app.app_context():
        try:
            update_job(job_id, {'status': 'processing'})
            output_filename = f"combine_{job_id}.mp4"
            output_path = os.path.join(output_folder, output_filename)
            
            # combine_videos doesn't return boolean, it raises exception on failure usually
            combine_videos(video1_path, video2_path, output_path)
            
            update_job(job_id, {'status': 'completed', 'output_url': f"/outputs/{output_filename}"})
        except Exception as e:
            update_job(job_id, {'status': 'error', 'message': str(e)})

def run_trim_task(job_id, video_path, start_time, end_time, output_folder):
    with app.app_context():
        try:
            update_job(job_id, {'status': 'processing'})
            output_filename = f"trim_{job_id}.mp4"
            output_path = os.path.join(output_folder, output_filename)
            
            trim_video(video_path, float(start_time), float(end_time), output_path)
            
            update_job(job_id, {'status': 'completed', 'output_url': f"/outputs/{output_filename}"})
        except Exception as e:
            update_job(job_id, {'status': 'error', 'message': str(e)})

def run_trim_audio_task(job_id, audio_path, start_time, end_time, output_folder):
    with app.app_context():
        try:
            update_job(job_id, {'status': 'processing'})
            # Determine extension from original file or default to mp3/aac. 
            # But trim_audio.py uses the extension provided in output path.
            # Let's try to preserve extension or default to mp3.
            base, ext = os.path.splitext(audio_path)
            if not ext: ext = ".mp3"
            
            output_filename = f"trim_audio_{job_id}{ext}"
            output_path = os.path.join(output_folder, output_filename)
            
            trim_audio(audio_path, float(start_time), float(end_time), output_path)
            
            update_job(job_id, {'status': 'completed', 'output_url': f"/outputs/{output_filename}"})
        except Exception as e:
            update_job(job_id, {'status': 'error', 'message': str(e)})

def run_tts_task(job_id, text, voice, speed, output_folder):
    with app.app_context():
        try:
            update_job(job_id, {'status': 'processing'})
            output_filename = f"tts_{job_id}.mp3"
            output_path = os.path.join(output_folder, output_filename)

            # Log start
            with open("tts_debug.log", "a", encoding="utf-8") as f:
                f.write(f"Starting TTS task for job {job_id}\n")

            text_to_speech(text, voice, float(speed), output_path)
            
            # Log end
            with open("tts_debug.log", "a", encoding="utf-8") as f:
                f.write(f"Finished TTS task for job {job_id}\n")

            update_job(job_id, {'status': 'completed', 'output_url': f"/outputs/{output_filename}"})
        except Exception as e:
            with open("tts_debug.log", "a", encoding="utf-8") as f:
                f.write(f"Exception in run_tts_task: {str(e)}\n")
            update_job(job_id, {'status': 'error', 'message': str(e)})

@app.route('/api/merge', methods=['POST'])
def merge():
    if 'video' not in request.files or 'audio' not in request.files:
        return jsonify({'error': 'Missing files'}), 400
    
    video = request.files['video']
    audio = request.files['audio']
    
    if video.filename == '' or audio.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    job_id = str(uuid.uuid4())
    
    # Use user-specific folders
    user_upload, user_output = get_user_folders()
    
    video_filename = secure_filename(f"{job_id}_{video.filename}")
    audio_filename = secure_filename(f"{job_id}_{audio.filename}")
    
    video_path = os.path.join(user_upload, video_filename)
    audio_path = os.path.join(user_upload, audio_filename)
    
    video.save(video_path)
    audio.save(audio_path)
    
    update_job(job_id, {'status': 'queued'})
    
    thread = threading.Thread(target=run_merge_task, args=(job_id, video_path, audio_path, user_output))
    thread.daemon = True
    thread.start()
    
    return jsonify({'job_id': job_id})

@app.route('/api/combine', methods=['POST'])
def combine():
    if 'video1' not in request.files or 'video2' not in request.files:
        return jsonify({'error': 'Missing files'}), 400
    
    video1 = request.files['video1']
    video2 = request.files['video2']
    
    job_id = str(uuid.uuid4())
    
    user_upload, user_output = get_user_folders()
    
    v1_filename = secure_filename(f"{job_id}_{video1.filename}")
    v2_filename = secure_filename(f"{job_id}_{video2.filename}")
    
    v1_path = os.path.join(user_upload, v1_filename)
    v2_path = os.path.join(user_upload, v2_filename)
    
    video1.save(v1_path)
    video2.save(v2_path)
    
    update_job(job_id, {'status': 'queued'})
    
    thread = threading.Thread(target=run_combine_task, args=(job_id, v1_path, v2_path, user_output))
    thread.daemon = True
    thread.start()
    
    return jsonify({'job_id': job_id})

@app.route('/api/trim', methods=['POST'])
def trim():
    if 'video' not in request.files:
        return jsonify({'error': 'Missing video file'}), 400
        
    video = request.files['video']
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')
    
    if not start_time or not end_time:
        return jsonify({'error': 'Missing start or end time'}), 400
        
    job_id = str(uuid.uuid4())
    user_upload, user_output = get_user_folders()
    
    video_filename = secure_filename(f"{job_id}_{video.filename}")
    video_path = os.path.join(user_upload, video_filename)
    
    video.save(video_path)
    
    update_job(job_id, {'status': 'queued'})
    
    thread = threading.Thread(target=run_trim_task, args=(job_id, video_path, start_time, end_time, user_output))
    thread.daemon = True
    thread.start()
    
    return jsonify({'job_id': job_id})

@app.route('/api/trim_audio', methods=['POST'])
def trim_audio_endpoint():
    if 'audio' not in request.files:
        return jsonify({'error': 'Missing audio file'}), 400
        
    audio = request.files['audio']
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')
    
    if not start_time or not end_time:
        return jsonify({'error': 'Missing start or end time'}), 400
        
    job_id = str(uuid.uuid4())
    user_upload, user_output = get_user_folders()
    
    audio_filename = secure_filename(f"{job_id}_{audio.filename}")
    audio_path = os.path.join(user_upload, audio_filename)
    
    audio.save(audio_path)
    
    update_job(job_id, {'status': 'queued'})
    
    thread = threading.Thread(target=run_trim_audio_task, args=(job_id, audio_path, start_time, end_time, user_output))
    thread.daemon = True
    thread.start()
    
    return jsonify({'job_id': job_id})

@app.route('/api/tts', methods=['POST'])
def tts_endpoint():
    text = request.form.get('text')
    voice = request.form.get('voice')
    speed = request.form.get('speed', 1.0)
    
    print(f"Received TTS request: text={repr(text[:10])}..., voice={voice}, speed={speed}") # DEBUG
    
    if not text or not voice:
        print("Missing text or voice") # DEBUG
        return jsonify({'error': 'Missing text or voice selection'}), 400
        
    job_id = str(uuid.uuid4())
    print(f"Created job {job_id}, starting thread") # DEBUG
    
    user_upload, user_output = get_user_folders()
    
    update_job(job_id, {'status': 'queued'})
    
    thread = threading.Thread(target=run_tts_task, args=(job_id, text, voice, speed, user_output))
    thread.daemon = True
    thread.start()
    
    return jsonify({'job_id': job_id})

if __name__ == '__main__':
    # Start cleanup task
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        cleanup_thread = threading.Thread(target=cleanup_temp_files)
        cleanup_thread.daemon = True
        cleanup_thread.start()
        
        # Start social media processor
        start_social_media_processor()
    
    app.run(debug=True, port=5000)
