import time
import psutil
import pythoncom
import threading
import os
from PyQt5.QtCore import QThread, pyqtSignal
from .app_tracker_utils import app_tracker_utils, save_session_data
from .config import settings, SYSTEM_PROCESSES

class TrackerThread(QThread):
    update_status_signal = pyqtSignal(str)
    update_list_signal = pyqtSignal(dict)
    update_debug_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.running = True
        self.last_check_time = time.time()
        self.inactivity_check_interval = 0.5  # Increase the frequency of checking
        self.last_ui_update = time.time()
        self.last_session_save = time.time()
        self.last_window_log = time.time()  # Add a timestamp for logging all open windows
        self.default_interval = 0.1  # Default sampling interval

    def run(self):
        pythoncom.CoInitialize()
        app_tracker_utils.log_debug("Tracker thread started.")

        # Start monitoring file changes in the user's home directory
        user_home_directory = os.path.expanduser("~")
        app_tracker_utils.start_monitoring(user_home_directory)

        while self.running:
            # Sleep based on user activity
            time.sleep(0.1 if app_tracker_utils.user_active else self.inactivity_check_interval)

            # Get the active application and window title
            new_app, new_pid, window_title = app_tracker_utils.get_active_app()
            current_time = time.time()

            # Log all open windows every 10 seconds for debugging purposes
            if current_time - self.last_window_log >= 10.0:
                threading.Thread(target=app_tracker_utils.log_all_open_windows).start()
                self.last_window_log = current_time

            # Log and update the current application if it has changed
            if new_app and new_app != app_tracker_utils.current_app:
                app_tracker_utils.log_debug(f"Switched to application: {new_app} - {window_title}")
                app_tracker_utils.current_app = new_app

            # Update user activity status
            app_tracker_utils.update_user_activity()

            # Update the active application tracking data
            if app_tracker_utils.current_app:
                elapsed_time = current_time - self.last_check_time
                if window_title:
                    app_tracker_utils.last_window_title = window_title
                else:
                    window_title = app_tracker_utils.last_window_title
                category = app_tracker_utils.categorize_activity(window_title)
                if category not in app_tracker_utils.active_apps:
                    app_tracker_utils.active_apps[category] = {}
                if app_tracker_utils.current_app not in app_tracker_utils.active_apps[category]:
                    app_tracker_utils.active_apps[category][app_tracker_utils.current_app] = {}
                if not isinstance(app_tracker_utils.active_apps[category][app_tracker_utils.current_app], dict):
                    app_tracker_utils.active_apps[category][app_tracker_utils.current_app] = {}
                if window_title not in app_tracker_utils.active_apps[category][app_tracker_utils.current_app]:
                    app_tracker_utils.active_apps[category][app_tracker_utils.current_app][window_title] = 0
                app_tracker_utils.active_apps[category][app_tracker_utils.current_app][window_title] += elapsed_time
                app_tracker_utils.log_debug(f"Updated active app: {app_tracker_utils.current_app}, window: {window_title}, elapsed time: {elapsed_time}")

            # Check if the application is active based on resource usage and other metrics
            if not app_tracker_utils.user_active and new_pid:
                threading.Thread(target=app_tracker_utils.is_application_active, args=(new_pid, new_pid == app_tracker_utils.current_app)).start()

            # Periodically check background activity
            if current_time - self.last_check_time >= 1.0:
                threading.Thread(target=app_tracker_utils.check_background_activity).start()

            self.last_check_time = current_time

            # Update the UI and debug log every second
            if current_time - self.last_ui_update >= 1.0:
                self.update_status_signal.emit(f"Tracking: {app_tracker_utils.current_app}")
                self.update_list_signal.emit(app_tracker_utils.active_apps.copy())
                self.update_debug_signal.emit("\n".join(app_tracker_utils.debug_logs))
                app_tracker_utils.log_debug("Emitted update signals.")
                self.last_ui_update = current_time

            # Save session data every 10 seconds
            if current_time - self.last_session_save >= 10.0:
                threading.Thread(target=save_session_data, args=(app_tracker_utils.active_apps,)).start()
                self.last_session_save = current_time

            # Adjust the sleep interval based on the sampling interval of the current application
            sleep_interval = app_tracker_utils.get_sampling_interval(new_pid) if new_pid else self.default_interval
            time.sleep(sleep_interval)

        app_tracker_utils.stop_monitoring()  # Stop monitoring file changes
        pythoncom.CoUninitialize()

    def stop(self):
        app_tracker_utils.log_debug("Tracker thread stopped.")
        self.running = False
        save_session_data(app_tracker_utils.active_apps)
        app_tracker_utils.stop_profiling()  # Stop profiling when the thread stops
