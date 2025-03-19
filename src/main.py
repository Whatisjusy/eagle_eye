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
from .app_tracker_utils import app_tracker_utils, save_session_data, load_session_data
from .gui import AppTracker
from .config import settings

# 🚨 Ignore Deprecation Warnings
import warnings
warnings.simplefilter("ignore", DeprecationWarning)

# ✅ Track Keyboard & Mouse Activity
def on_activity(_):
    global last_active_time, user_active
    last_active_time = time.time()
    user_active = True

keyboard_listener = keyboard.Listener(on_press=on_activity)
mouse_listener = mouse.Listener(on_click=on_activity, on_scroll=on_activity)

if __name__ == "__main__":
    keyboard_listener.start()
    mouse_listener.start()
    app = QApplication(sys.argv)
    global tracker
    tracker = AppTracker()
    tracker.show()
    sys.exit(app.exec_())