import csv
import os
from werkzeug.security import generate_password_hash, check_password_hash

USER_DB_FILE = 'users.csv'

def init_db():
    if not os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['username', 'password_hash'])

def register_user(username, password):
    init_db()
    
    # Check if user exists
    with open(USER_DB_FILE, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['username'] == username:
                return False, "User already exists"

    # Add new user
    with open(USER_DB_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([username, generate_password_hash(password)])
        
    # Create user directories
    os.makedirs(os.path.join('uploads', username), exist_ok=True)
    os.makedirs(os.path.join('outputs', username), exist_ok=True)
    
    return True, "Registration successful"

def authenticate_user(username, password):
    init_db()
    
    with open(USER_DB_FILE, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['username'] == username:
                if check_password_hash(row['password_hash'], password):
                    return True
    return False
