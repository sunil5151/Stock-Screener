import json
import os
import datetime
import uuid

HISTORY_DIR = os.path.join(os.path.dirname(__file__), "history")
os.makedirs(HISTORY_DIR, exist_ok=True)

def get_user_history_path(username):
    """Get path to user's history file"""
    return os.path.join(HISTORY_DIR, f"{username}_history.json")

def load_user_history(username):
    """Load user's analysis history"""
    path = get_user_history_path(username)
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)

def save_user_history(username, history):
    """Save user's analysis history"""
    path = get_user_history_path(username)
    with open(path, "w") as f:
        json.dump(history, f, indent=2)

def add_history_entry(username, original_filename, file_path, results=None):
    """Add a new entry to user's history"""
    history = load_user_history(username)
    
    # Generate a unique ID for this analysis
    upload_id = str(uuid.uuid4())
    
    # Create history entry
    entry = {
        "upload_id": upload_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "original_filename": original_filename,
        "file_path": file_path,
        "processed": False,
        "results": None,
        "chart_paths": {}
    }
    
    # Add results if provided
    if results:
        entry["processed"] = True
        entry["results"] = {
            "accuracy": results.get("accuracy_results", {}),
            "signals_count": len(results.get("signals", [])),
        }
    
    # Add to history and save
    history.append(entry)
    save_user_history(username, history)
    
    return upload_id

def update_history_entry(username, upload_id, data):
    """Update an existing history entry"""
    history = load_user_history(username)
    
    for entry in history:
        if entry["upload_id"] == upload_id:
            entry.update(data)
            save_user_history(username, history)
            return True
    
    return False

def get_history_entry(username, upload_id):
    """Get a specific history entry"""
    history = load_user_history(username)
    
    for entry in history:
        if entry["upload_id"] == upload_id:
            return entry
    
    return None

def delete_history_entry(username, upload_id):
    """Delete a history entry and associated files"""
    history = load_user_history(username)
    entry = None
    
    # Find and remove the entry
    for i, item in enumerate(history):
        if item["upload_id"] == upload_id:
            entry = history.pop(i)
            break
    
    if entry:
        # Delete associated files
        if os.path.exists(entry["file_path"]):
            os.remove(entry["file_path"])
        
        # Delete chart files if they exist
        for format_type, path in entry.get("chart_paths", {}).items():
            if os.path.exists(path):
                os.remove(path)
        
        # Save updated history
        save_user_history(username, history)
        return True
    
    return False