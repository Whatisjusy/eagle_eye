import sys
import time
import json
import os
import psutil
import win32gui
import win32process
import win32api
import pythoncom
import ctypes
from ctypes import wintypes
from pynput import keyboard, mouse
from PyQt5.QtWidgets import QApplication

# Ensure the src directory is in the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.app_tracker_utils import app_tracker_utils, save_session_data, load_session_data
from src.gui import AppTracker
from src.config import settings

# 🚨 Ignore Deprecation Warnings
import warnings
warnings.simplefilter("ignore", DeprecationWarning)

# ✅ Track Keyboard & Mouse Activity
def on_activity(event):
    global last_active_time, user_active
    last_active_time = time.time()
    user_active = True
    app_tracker_utils.log_debug(f"User interaction detected: {event}")

keyboard_listener = keyboard.Listener(on_press=on_activity)
mouse_listener = mouse.Listener(on_click=on_activity)  # Remove on_scroll

def main():
    app_tracker_utils.log_debug("Application started.")
    app_tracker_utils.set_tracker_pid(os.getpid())  # Set the tracker's PID
    keyboard_listener.start()
    mouse_listener.start()
    app = QApplication(sys.argv)
    global tracker
    tracker = AppTracker()
    tracker.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()