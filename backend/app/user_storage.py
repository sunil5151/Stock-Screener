import json
import os
from passlib.hash import sha256_crypt

USER_FILE = "users.json"

def get_user_file_path():
    # Store users.json in the same directory as this script
    return os.path.join(os.path.dirname(__file__), USER_FILE)

def load_users():
    path = get_user_file_path()
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

def save_users(users):
    path = get_user_file_path()
    with open(path, "w") as f:
        json.dump(users, f, indent=2)

def register_user(username, password, email=None):
    users = load_users()
    if username in users:
        return False, "Username already exists"
    
    # First user is automatically an admin
    is_admin = len(users) == 0
    
    users[username] = {
        "password": sha256_crypt.hash(password),
        "email": email,
        "is_admin": is_admin
    }
    
    save_users(users)
    return True, "User registered successfully"

def validate_user(username, password):
    users = load_users()
    if username not in users:
        return False
    
    # Handle both old format (string password hash) and new format (dict with password hash)
    user_data = users[username]
    if isinstance(user_data, str):
        return sha256_crypt.verify(password, user_data)
    else:
        return sha256_crypt.verify(password, user_data["password"])

def get_user_data(username):
    users = load_users()
    if username not in users:
        return None
    
    user_data = users[username]
    # Handle old format (string password hash)
    if isinstance(user_data, str):
        return {"password": user_data, "email": None, "is_admin": False}
    return user_data

def is_admin(username):
    user_data = get_user_data(username)
    if not user_data:
        return False
    return user_data.get("is_admin", False)

def update_user_email(username, email):
    users = load_users()
    if username not in users:
        return False
    
    # Handle old format (string password hash)
    if isinstance(users[username], str):
        password_hash = users[username]
        users[username] = {
            "password": password_hash,
            "email": email,
            "is_admin": False
        }
    else:
        users[username]["email"] = email
    
    save_users(users)
    return True

def delete_user(username):
    users = load_users()
    if username not in users:
        return False
    
    del users[username]
    save_users(users)
    return True