import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "webhook": "",
    "auto_refresh": True,
    "refresh_interval": "10"
}

def save_config(data):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        print("Save error:", e)
        return False

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
    except Exception:
        return DEFAULT_CONFIG.copy()

    for k, v in DEFAULT_CONFIG.items():
        if k not in data:
            data[k] = v
    return data