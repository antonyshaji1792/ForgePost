import json
import os

SETTINGS_FILE = 'user_settings.json'

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {}
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_settings(all_settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(all_settings, f, indent=4)

def get_user_settings(username):
    all_settings = load_settings()
    return all_settings.get(username, {})

def update_user_settings(username, new_settings):
    all_settings = load_settings()
    if username not in all_settings:
        all_settings[username] = {}
    
    # Update existing settings with new values
    all_settings[username].update(new_settings)
    save_settings(all_settings)
