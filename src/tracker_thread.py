import time
import psutil
import pythoncom
from PyQt5.QtCore import QThread, pyqtSignal
from .app_tracker_utils import app_tracker_utils, save_session_data
from .config import settings, system_processes

class TrackerThread(QThread):
    update_status_signal = pyqtSignal(str)
    update_list_signal = pyqtSignal(dict)
    update_debug_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.running = True
        self.last_check_time = time.time()
        self.inactivity_check_interval = 1
        self.last_ui_update = time.time()

    def run(self):
        pythoncom.CoInitialize()
        app_tracker_utils.log_debug("Tracker thread started.")

        while self.running:
            time.sleep(0.2 if app_tracker_utils.user_active else self.inactivity_check_interval)

            new_app, new_pid, window_title = app_tracker_utils.get_active_app()
            current_time = time.time()

            if new_app and new_app != app_tracker_utils.current_app:
                app_tracker_utils.log_debug(f"Switched to application: {new_app} - {window_title}")
                app_tracker_utils.current_app = new_app

            if new_pid:
                cpu_usage, mem_usage, io_usage = app_tracker_utils.get_app_cpu_usage(new_pid)
                if cpu_usage is not None:
                    avg_cpu, avg_mem, avg_io = app_tracker_utils.update_baseline(new_pid, cpu_usage, mem_usage, io_usage)
                    factor = 1.3
                    if (cpu_usage > factor * avg_cpu or 
                        mem_usage > factor * avg_mem or 
                        io_usage > factor * avg_io):
                        app_tracker_utils.user_active = True
                        app_tracker_utils.last_active_time = current_time
                        app_tracker_utils.log_debug("Relative resource usage suggests app is active (dynamic threshold).")

            if not app_tracker_utils.user_active:
                for proc in psutil.process_iter(attrs=['pid', 'name']):
                    if proc.info['name'] not in system_processes:
                        cpu_usage, mem_usage, io_usage = app_tracker_utils.get_app_cpu_usage(proc.info['pid'])
                        if cpu_usage is not None:
                            avg_cpu, avg_mem, avg_io = app_tracker_utils.update_baseline(proc.info['pid'], cpu_usage, mem_usage, io_usage)
                            if (cpu_usage > 1.3 * avg_cpu or 
                                mem_usage > 1.3 * avg_mem or 
                                io_usage > 1.3 * avg_io):
                                app_tracker_utils.user_active = True
                                app_tracker_utils.last_active_time = current_time
                                app_tracker_utils.log_debug(f"Relative resource usage suggests {proc.info['name']} is active.")

            if current_time - app_tracker_utils.last_active_time > settings["inactivity_timeout"]:
                if app_tracker_utils.user_active:
                    app_tracker_utils.log_debug("User is now inactive.")
                app_tracker_utils.user_active = False

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

            self.last_check_time = current_time

            if current_time - self.last_ui_update >= 1.0:
                self.update_status_signal.emit(f"Tracking: {app_tracker_utils.current_app}")
                self.update_list_signal.emit(app_tracker_utils.active_apps.copy())
                self.update_debug_signal.emit("\n".join(app_tracker_utils.debug_logs))
                self.last_ui_update = current_time

            if int(current_time) % 10 == 0:
                save_session_data()

        pythoncom.CoUninitialize()

    def stop(self):
        app_tracker_utils.log_debug("Tracker thread stopped.")
        self.running = False
        save_session_data()
