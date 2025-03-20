import json
import os

# ✅ File Paths
FILE_PATHS = {
    "DATA_FILE": "history.json",
    "SETTINGS_FILE": "settings.json",
    "DEBUG_FILE": "debug.log"
}

# ✅ Default Settings
DEFAULTS = {
    "inactivity_timeout": 10,  
    "cpu_threshold": 10,  
    "mem_threshold": 5,   # Example value, adjust as needed.
    "io_threshold": 1000000,  # Example value for IO.
    "grace_period": 5,  
    "max_progress_time": 10 * 3600  
}

# ✅ Load or Initialize Settings
def load_settings():
    if os.path.exists(FILE_PATHS["SETTINGS_FILE"]):
        try:
            with open(FILE_PATHS["SETTINGS_FILE"], "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # Log the error and return default settings
            print("Error decoding JSON from settings file. Using default settings.")
            return DEFAULTS.copy()
    return DEFAULTS.copy()

def reset_settings():
    with open(FILE_PATHS["SETTINGS_FILE"], "w") as f:
        json.dump(DEFAULTS, f)
    return DEFAULTS.copy()

settings = load_settings()

# ✅ List of System Processes to Exclude
SYSTEM_PROCESSES = [
    "System Idle Process", "System", "Registry", "smss.exe", "csrss.exe", "wininit.exe",
    "services.exe", "lsass.exe", "svchost.exe", "winlogon.exe", "SearchUI.exe", "ShellExperienceHost.exe", "RuntimeBroker.exe", "dwm.exe"
]
