import time
import json
import os
import psutil
import win32gui
import win32process
import win32api
import ctypes
from ctypes import wintypes
import logging
from .config import DATA_FILE, SETTINGS_FILE, DEBUG_FILE, default_settings, load_settings, settings, system_processes
from .app_tracker_utils import AppTrackerUtilities, get_app_cpu_usage, save_session_data, load_session_data

# Initialize the utilities class
app_tracker_utils = AppTrackerUtilities()

# ✅ Initialize Session Data
app_tracker_utils.active_apps = load_session_data()
