import os
import datetime

LOG_FILE = "agent.log"

def log_event(message, category="INFO"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] [{category}] {message}\n"
    
    # Print to console for normal terminal runs
    print(message)
    
    # Write to log file for background task tracking
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted_msg)
    except Exception as e:
        print(f"Error writing to log: {e}")

def clear_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(f"--- Log Cleared at {datetime.datetime.now()} ---\n")
