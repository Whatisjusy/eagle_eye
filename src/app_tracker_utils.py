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
from .config import FILE_PATHS, DEFAULTS, load_settings, settings, SYSTEM_PROCESSES
import threading
import win32con
import win32event
import win32file
import cProfile  # Add import for cProfile
import pstats  # Add import for pstats

DATA_FILE = FILE_PATHS["DATA_FILE"]
SETTINGS_FILE = FILE_PATHS["SETTINGS_FILE"]
DEBUG_FILE = FILE_PATHS["DEBUG_FILE"]

# ✅ Initialize Session Data
def load_session_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_session_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# Initialize the utilities class
class AppTrackerUtilities:
    def __init__(self):
        self.log_lock = threading.Lock()  # Add a lock for thread-safe logging
        self.activity_lock = threading.Lock()  # Add a lock for thread-safe activity score calculations
        self.stop_event = threading.Event()  # Event to signal stopping the monitoring
        self.profiler = cProfile.Profile()  # Add a profiler instance
        self.profiler.enable()  # Enable profiling
        self.active_apps = {}
        self.current_app = None
        self.user_active = False
        self.last_active_time = time.time()
        self.app_name_cache = {}
        self.debug_logs = []
        self.baseline = {}
        self.resource_usage = {}
        self.thresholds = {}
        self.tracker_pid = None  # Add a variable to store the tracker's PID
        self.active_pids = set()  # Add a set to store active PIDs
        self.known_active_apps = {}  # Add a dictionary to store known active applications
        self.sampling_intervals = {}  # Add a dictionary to store sampling intervals for each PID
        self.default_interval = 1.0  # Default sampling interval in seconds
        self.max_interval = 10.0  # Maximum sampling interval in seconds
        self.min_interval = 0.5  # Minimum sampling interval in seconds
        self.aggregation_interval = 5.0  # Aggregation interval in seconds
        self.aggregated_data = {}        # Dictionary to store aggregated CPU and I/O data
        self.foreground_weight = 2.0  # Weight for foreground applications
        self.background_weight = 1.0  # Weight for background applications
        self.cpu_threshold = 5.0  # CPU usage threshold percentage
        self.io_threshold = 1048576  # I/O usage threshold in bytes (1 MB)
        self.top_n = 5  # Number of top apps to focus detailed tracking on
        self.top_apps = []  # List to store top N apps
        logging.basicConfig(filename=DEBUG_FILE, level=logging.DEBUG, format='%(asctime)s %(message)s')
        self.log_debug("AppTrackerUtilities initialized.")
        self.cache = {}  # Cache to store recent values
        self.batch_size = 10  # Batch size for processing
        self.batch_data = []  # List to store batch data
        self.inactivity_timeout = settings.get("inactivity_timeout", 300)  # Default to 300 seconds if not set

    def save_profile_stats(self):
        self.profiler.disable()
        with open("app_tracker_profile_stats.txt", "w") as f:
            ps = pstats.Stats(self.profiler, stream=f)
            ps.sort_stats(pstats.SortKey.CUMULATIVE)
            ps.print_stats()
        # Do not re-enable the profiler here

    def log_debug(self, message, error=False):
        with self.log_lock:  # Ensure thread-safe logging
            if error:
                logging.error(message)
            else:
                logging.debug(message)
            self.debug_logs.append(message)
            if len(self.debug_logs) > 1000:  # Limit the log size
                self.debug_logs.pop(0)
        self.save_profile_stats()  # Save profiling stats after logging

    def stop_profiling(self):
        self.save_profile_stats()  # Save profiling stats before stopping
        self.profiler.disable()  # Disable profiling

    def get_friendly_app_name(self, process):
        try:
            # Try to get the executable path and derive the friendly name
            exe_path = process.exe()
            friendly_name = os.path.basename(exe_path).rsplit('.', 1)[0]
            return friendly_name
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            # Fallback to process name if exe path is not accessible
            return process.name().rsplit('.', 1)[0]

    def set_tracker_pid(self, pid):
        self.tracker_pid = pid
        self.log_debug(f"Tracker PID set to {pid}")

    def get_active_app(self):
        hwnd = win32gui.GetForegroundWindow()
        if hwnd == 0 or not win32gui.IsWindowVisible(hwnd) or not win32gui.GetWindowText(hwnd):
            self.log_debug("No active window detected or window is not visible.")
            return None, None, None
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if pid == self.tracker_pid:  # Exclude the tracker's PID
            return None, None, None  # Skip logging for the tracker's PID
        self.active_pids.add(pid)  # Add the PID to the active PIDs set
        self.known_active_apps[pid] = time.time()  # Update the known active applications
        self.log_debug(f"Foreground window handle: {hwnd}, PID: {pid}")
        try:
            process = psutil.Process(pid)
            friendly_app_name = self.get_friendly_app_name(process)
            window_title = win32gui.GetWindowText(hwnd)
            self.log_debug(f"Active window detected: {friendly_app_name} - {window_title}")
            return friendly_app_name, pid, window_title
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            self.log_debug(f"Error detecting active window: {e}", error=True)
            return None, None, None

    def log_all_open_windows(self):
        def enum_window_callback(hwnd, results):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                results.append((hwnd, pid, win32gui.GetWindowText(hwnd)))
        results = []
        win32gui.EnumWindows(enum_window_callback, results)
        for hwnd, pid, title in results:
            self.log_debug(f"Open window: hwnd={hwnd}, pid={pid}, title={title}")

    def categorize_activity(self, window_title):
        # Example categorization logic based on window title
        if "Visual Studio Code" in window_title:
            return "Development"
        elif "Chrome" in window_title or "Firefox" in window_title:
            return "Browsing"
        elif "Word" in window_title or "Excel" in window_title:
            return "Office"
        else:
            return "Other"

    def update_baseline(self, pid, cpu_usage, io_usage):
        if pid not in self.baseline:
            self.baseline[pid] = {
                "cpu": [],
                "io": []
            }
        self.baseline[pid]["cpu"].append(cpu_usage)
        self.baseline[pid]["io"].append(io_usage)
        if len(self.baseline[pid]["cpu"]) > 10:
            self.baseline[pid]["cpu"].pop(0)
            self.baseline[pid]["io"].pop(0)
        avg_cpu = sum(self.baseline[pid]["cpu"]) / len(self.baseline[pid]["cpu"])
        avg_io = sum(self.baseline[pid]["io"]) / len(self.baseline[pid]["io"])
        self.log_debug(f"Updated baseline for PID {pid}: avg_cpu={avg_cpu}, avg_io={avg_io}")
        return avg_cpu, avg_io

    def aggregate_metrics(self, pid, cpu_usage, io_usage):
        if pid not in self.aggregated_data:
            self.aggregated_data[pid] = {
                "cpu": [],
                "io": [],
                "last_time": time.time()
            }
        self.aggregated_data[pid]["cpu"].append(cpu_usage)
        self.aggregated_data[pid]["io"].append(io_usage)
        current_time = time.time()
        if current_time - self.aggregated_data[pid]["last_time"] >= self.aggregation_interval:
            avg_cpu = sum(self.aggregated_data[pid]["cpu"]) / len(self.aggregated_data[pid]["cpu"])
            avg_io = sum(self.aggregated_data[pid]["io"]) / len(self.aggregated_data[pid]["io"])
            # Reset aggregation data for next interval
            self.aggregated_data[pid]["cpu"] = []
            self.aggregated_data[pid]["io"] = []
            self.aggregated_data[pid]["last_time"] = current_time
            self.log_debug(f"Aggregated metrics for PID {pid}: avg_cpu={avg_cpu}, avg_io={avg_io}")
            return avg_cpu, avg_io
        return None, None

    def cache_metrics(self, pid, cpu_usage, io_usage):
        self.cache[pid] = (cpu_usage, io_usage)
        self.log_debug(f"Cached metrics for PID {pid}: CPU={cpu_usage}%, IO={io_usage} bytes")

    def process_batch_data(self):
        if len(self.batch_data) >= self.batch_size:
            for pid, cpu_usage, io_usage in self.batch_data:
                self.calculate_activity_score(pid, cpu_usage, io_usage, pid in self.active_pids)
            self.batch_data = []
            self.log_debug("Processed batch data")

    def get_app_resource_usage(self, pid):
        try:
            if pid in self.cache:
                cpu_usage, io_usage = self.cache[pid]
                self.log_debug(f"Using cached resource usage for PID {pid}: CPU={cpu_usage}%, IO={io_usage} bytes")
            else:
                process = psutil.Process(pid)
                cpu_usage = process.cpu_percent(interval=1)
                io_counters = process.io_counters()
                io_usage = io_counters.read_bytes + io_counters.write_bytes
                self.cache_metrics(pid, cpu_usage, io_usage)
                self.log_debug(f"Raw resource usage for PID {pid}: CPU={cpu_usage}%, IO={io_usage} bytes")
            self.batch_data.append((pid, cpu_usage, io_usage))
            self.process_batch_data()
            return self.aggregate_metrics(pid, cpu_usage, io_usage)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            self.log_debug(f"Error getting resource usage for PID {pid}: {e}", error=True)
            return None, None

    def update_thresholds(self, pid, avg_cpu, avg_io):
        if pid not in self.thresholds:
            self.thresholds[pid] = {
                "cpu": 1.3 * avg_cpu,
                "io": 1.3 * avg_io
            }
        else:
            self.thresholds[pid]["cpu"] = 0.9 * self.thresholds[pid]["cpu"] + 0.1 * (1.3 * avg_cpu)
            self.thresholds[pid]["io"] = 0.9 * self.thresholds[pid]["io"] + 0.1 * (1.3 * avg_io)
        self.log_debug(f"Updated thresholds for PID {pid}: cpu_threshold={self.thresholds[pid]['cpu']}, io_threshold={self.thresholds[pid]['io']}")

    def adjust_sampling_interval(self, pid, activity_score):
        self.log_debug(f"Updated thresholds for PID {pid}: cpu_threshold={self.thresholds[pid]['cpu']}, io_threshold={self.thresholds[pid]['io']}")

    def adjust_sampling_interval(self, pid, activity_score):
        if activity_score >= 2:
            self.sampling_intervals[pid] = self.min_interval
        elif activity_score == 1:
            self.sampling_intervals[pid] = self.default_interval
        else:
            self.sampling_intervals[pid] = min(self.sampling_intervals.get(pid, self.default_interval) * 2, self.max_interval)
        self.log_debug(f"Adjusted sampling interval for PID {pid}: {self.sampling_intervals[pid]} seconds")

    def get_sampling_interval(self, pid):
        return self.sampling_intervals.get(pid, self.default_interval)

    def is_above_threshold(self, cpu_usage, io_usage):
        return cpu_usage > self.cpu_threshold or io_usage > self.io_threshold

    def update_top_apps(self, pid, cpu_usage, io_usage):
        app_data = (pid, cpu_usage, io_usage)
        self.top_apps.append(app_data)
        self.top_apps.sort(key=lambda x: (x[1], x[2]), reverse=True)  # Sort by CPU and I/O usage
        self.top_apps = self.top_apps[:self.top_n]  # Keep only top N apps
        self.log_debug(f"Updated top apps: {self.top_apps}")

    def calculate_activity_score(self, pid, cpu_usage, io_usage, is_foreground):
        with self.activity_lock:  # Ensure thread-safe activity score calculations
            if not self.is_above_threshold(cpu_usage, io_usage):
                self.log_debug(f"PID {pid} below threshold: CPU={cpu_usage}%, IO={io_usage} bytes")
                return 0  # Return 0 if the app is below the resource threshold
            avg_cpu, avg_io = self.update_baseline(pid, cpu_usage, io_usage)
            self.update_thresholds(pid, avg_cpu, avg_io)
            score = 0
            weight = self.foreground_weight if is_foreground else self.background_weight
            if cpu_usage > self.thresholds[pid]["cpu"]:
                score += 1 * weight
            if io_usage > self.thresholds[pid]["io"]:
                score += 1 * weight
            if self.user_active:
                score += 1 * self.user_activity_weight
            self.adjust_sampling_interval(pid, score)  # Adjust the sampling interval based on the activity score
            self.update_top_apps(pid, cpu_usage, io_usage)  # Update the top apps list
            self.log_debug(f"Activity score for PID {pid}: {score} (CPU: {cpu_usage}, IO: {io_usage}, User Active: {self.user_active}, Foreground: {is_foreground})")
            return score

    def check_background_activity(self):
        for pid in list(self.known_active_apps.keys()):
            if pid == self.tracker_pid:
                continue
            cpu_usage, io_usage = self.get_app_resource_usage(pid)
            if cpu_usage is not None and io_usage is not None:
                score = self.calculate_activity_score(pid, cpu_usage, io_usage, False)
                if score >= 2:
                    self.log_debug(f"Background activity detected for PID {pid}: score={score}")
                    return True
            else:
                # Remove the PID from known active apps if the process no longer exists
                del self.known_active_apps[pid]
        return False

    def is_application_active(self, pid, is_foreground):
        cpu_usage, io_usage = self.get_app_resource_usage(pid)
        if cpu_usage is None or io_usage is None:
            return False
        score = self.calculate_activity_score(pid, cpu_usage, io_usage, is_foreground)
        self.log_debug(f"Activity score for PID {pid}: {score}")
        if score >= 2:
            return True
        return self.check_background_activity()

    def monitor_file_changes(self, directory):
        change_handle = win32file.FindFirstChangeNotification(
            directory,
            0,
            win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
            win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
            win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |
            win32con.FILE_NOTIFY_CHANGE_SIZE |
            win32con.FILE_NOTIFY_CHANGE_LAST_WRITE |
            win32con.FILE_NOTIFY_CHANGE_SECURITY
        )
        try:
            while not self.stop_event.is_set():
                result = win32event.WaitForSingleObject(change_handle, 500)
                if result == win32con.WAIT_OBJECT_0:
                    self.log_debug(f"Change detected in directory: {directory}")
                    win32file.FindNextChangeNotification(change_handle)
        finally:
            win32file.FindCloseChangeNotification(change_handle)

    def start_monitoring(self, directory):
        self.stop_event.clear()
        threading.Thread(target=self.monitor_file_changes, args=(directory,)).start()

    def stop_monitoring(self):
        self.stop_event.set()

    def update_user_activity(self):
        current_time = time.time()
        if current_time - self.last_active_time > self.inactivity_timeout:
            if self.user_active:
                self.log_debug("User is now inactive.")
            self.user_active = False
        else:
            self.user_active = True

app_tracker_utils = AppTrackerUtilities()

app_tracker_utils.active_apps = load_session_data()

