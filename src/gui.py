from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QPushButton, QSpinBox, QTreeWidget, QTreeWidgetItem, QListWidget,
    QTabWidget, QMessageBox, QFormLayout, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import pyqtSignal, Qt
import logging
from .app_tracker_utils import app_tracker_utils, save_session_data, load_session_data
from .tracker_thread import TrackerThread
from .config import settings, FILE_PATHS

# Initialize logging
logging.basicConfig(filename=FILE_PATHS["DEBUG_FILE"], level=logging.DEBUG, format='%(asctime)s %(message)s')

class AppTracker(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.tracker_thread = TrackerThread()
        self.tracker_thread.update_status_signal.connect(self.update_status)
        self.tracker_thread.update_list_signal.connect(self.update_live_list)
        self.tracker_thread.update_debug_signal.connect(self.update_debug_log)
        self.tracker_thread.start()
        logging.info("AppTracker initialized and tracker thread started.")

    def initUI(self):
        try:
            self.setWindowTitle("Active App Tracker")
            self.setGeometry(100, 100, 500, 600)

            self.tabs = QTabWidget()
            self.main_tab = QWidget()
            self.debug_tab = QWidget()
            self.settings_tab = QWidget()
            self.tabs.addTab(self.main_tab, "Live Tracking")
            self.tabs.addTab(self.debug_tab, "Debug Log")
            self.tabs.addTab(self.settings_tab, "Settings")

            layout = QVBoxLayout(self.main_tab)
            self.status_label = QLabel("Tracking Active Applications...")
            layout.addWidget(self.status_label)

            self.live_tree = QTreeWidget()
            self.live_tree.setHeaderLabels(["Application", "Window", "Time Spent"])
            self.live_tree.header().setStyleSheet("QHeaderView::section { background-color: #444444; color: #ffffff; }")
            layout.addWidget(self.live_tree)

            self.reset_button = QPushButton("Reset Progress")
            self.reset_button.setToolTip("Click to reset the progress tracking")
            self.reset_button.clicked.connect(self.reset_progress)
            layout.addWidget(self.reset_button)

            self.end_session_button = QPushButton("End Session")
            self.end_session_button.setToolTip("Click to end the current session and calculate total wage")
            self.end_session_button.clicked.connect(self.end_session)
            layout.addWidget(self.end_session_button)

            debug_layout = QVBoxLayout(self.debug_tab)
            self.debug_list = QListWidget()
            debug_layout.addWidget(self.debug_list)

            self.copy_log_button = QPushButton("Copy Log")
            self.copy_log_button.setToolTip("Click to copy the debug log to clipboard")
            self.copy_log_button.clicked.connect(self.copy_log_to_clipboard)
            debug_layout.addWidget(self.copy_log_button)

            settings_layout = QFormLayout(self.settings_tab)

            self.inactivity_box = QSpinBox()
            self.inactivity_box.setRange(5, 60)
            self.inactivity_box.setValue(settings["inactivity_timeout"])
            self.inactivity_box.setToolTip("Set the inactivity timeout in seconds")
            self.inactivity_box.valueChanged.connect(self.update_settings)

            self.cpu_box = QSpinBox()
            self.cpu_box.setRange(1, 100)
            self.cpu_box.setValue(settings["cpu_threshold"])
            self.cpu_box.setToolTip("Set the CPU usage threshold percentage")
            self.cpu_box.valueChanged.connect(self.update_settings)

            self.hourly_wage_box = QSpinBox()
            self.hourly_wage_box.setRange(1, 1000)
            self.hourly_wage_box.setValue(settings.get("hourly_wage", 10))
            self.hourly_wage_box.setToolTip("Set your hourly wage in dollars")
            self.hourly_wage_box.valueChanged.connect(self.update_settings)

            settings_layout.addRow(QLabel("Inactivity Timeout (sec):"), self.inactivity_box)
            settings_layout.addRow(QLabel("CPU Threshold (%):"), self.cpu_box)
            settings_layout.addRow(QLabel("Hourly Wage ($):"), self.hourly_wage_box)

            self.settings_tab.setLayout(settings_layout)
            main_layout = QVBoxLayout()
            main_layout.addWidget(self.tabs)
            self.setLayout(main_layout)

            self.setStyleSheet("""
                QWidget {
                    background-color: #2e2e2e;
                    color: #ffffff;
                }
                QTabWidget::pane {
                    border: 1px solid #444444;
                }
                QTabBar::tab {
                    background: #444444;
                    border: 1px solid #444444;
                    padding: 10px;
                }
                QTabBar::tab:selected {
                    background: #2e2e2e;
                    border-bottom-color: #2e2e2e;
                }
                QLabel, QSpinBox, QPushButton, QTreeWidget, QTreeWidget::item {
                    background-color: #2e2e2e;
                    color: #ffffff;
                }
                QTreeWidget::item:selected {
                    background-color: #444444;
                    color: #ffffff;
                }
                QPushButton {
                    border: 1px solid #444444;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #444444;
                }
            """)

            logging.info("UI initialized.")
        except Exception as e:
            logging.error(f"Error initializing UI: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while initializing the UI: {e}")

    def copy_log_to_clipboard(self):
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText("\n".join(app_tracker_utils.debug_logs))
            QMessageBox.information(self, "Log Copied", "Debug log has been copied to clipboard.")
            logging.info("Debug log copied to clipboard.")
        except Exception as e:
            logging.error(f"Error copying log to clipboard: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while copying the log to clipboard: {e}")

    def update_settings(self):
        try:
            settings["inactivity_timeout"] = self.inactivity_box.value()
            settings["cpu_threshold"] = self.cpu_box.value()
            settings["hourly_wage"] = self.hourly_wage_box.value()
            with open(FILE_PATHS["SETTINGS_FILE"], "w") as f:
                json.dump(settings, f)
            logging.info("Settings updated.")
        except Exception as e:
            logging.error(f"Error updating settings: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while updating the settings: {e}")

    def update_status(self, text):
        try:
            self.status_label.setText(text)
            logging.debug(f"Status updated: {text}")
        except Exception as e:
            logging.error(f"Error updating status: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while updating the status: {e}")

    def update_live_list(self, apps):
        try:
            self.live_tree.clear()
            for category, app_times in apps.items():
                for app, window_times in app_times.items():
                    if not isinstance(window_times, dict):
                        app_tracker_utils.log_debug(f"Error: window_times is not a dict for app {app} in category {category}: {window_times}", error=True)
                        continue
                    app_item = self.find_or_create_app_item(app)
                    total_time = 0
                    for window, time_spent in window_times.items():
                        formatted_time = self.format_time(time_spent)
                        window_item = self.find_or_create_window_item(app_item, window)
                        window_item.setText(2, formatted_time)
                        total_time += time_spent
                    app_item.setText(2, self.format_time(total_time))
                    app_item.setExpanded(True)
            logging.debug("Live list updated.")
        except Exception as e:
            logging.error(f"Error updating live list: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while updating the live list: {e}")

    def find_or_create_app_item(self, app):
        try:
            for i in range(self.live_tree.topLevelItemCount()):
                item = self.live_tree.topLevelItem(i)
                if item.text(0) == app:
                    return item
            app_item = QTreeWidgetItem([app])
            self.live_tree.addTopLevelItem(app_item)
            return app_item
        except Exception as e:
            logging.error(f"Error finding or creating app item: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while finding or creating the app item: {e}")
            return None

    def find_or_create_window_item(self, app_item, window):
        try:
            for i in range(app_item.childCount()):
                item = app_item.child(i)
                if item.text(1) == window:
                    return item
            window_item = QTreeWidgetItem([app_item.text(0), window])
            app_item.addChild(window_item)
            return window_item
        except Exception as e:
            logging.error(f"Error finding or creating window item: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while finding or creating the window item: {e}")
            return None

    def format_time(self, seconds):
        try:
            hours, remainder = divmod(seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        except Exception as e:
            logging.error(f"Error formatting time: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while formatting the time: {e}")
            return "0h 0m 0s"

    def update_debug_log(self, log_text):
        try:
            self.debug_list.clear()
            self.debug_list.addItems(log_text.split("\n"))
            logging.debug("Debug log updated.")
        except Exception as e:
            logging.error(f"Error updating debug log: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while updating the debug log: {e}")

    def reset_progress(self):
        try:
            app_tracker_utils.active_apps = {}
            self.update_live_list(app_tracker_utils.active_apps)
            logging.info("Progress reset.")
        except Exception as e:
            logging.error(f"Error resetting progress: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while resetting the progress: {e}")

    def closeEvent(self, event):
        try:
            self.tracker_thread.stop()
            event.accept()
            logging.info("Application closed.")
        except Exception as e:
            logging.error(f"Error closing application: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while closing the application: {e}")

    def end_session(self):
        try:
            self.tracker_thread.stop()
            dialog = EndSessionDialog(app_tracker_utils.active_apps, settings.get("hourly_wage", 10), self)
            if dialog.exec_() == QDialog.Accepted:
                self.reset_progress()
            logging.info("Session ended.")
        except Exception as e:
            logging.error(f"Error ending session: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while ending the session: {e}")

class EndSessionDialog(QDialog):
    def __init__(self, apps, hourly_wage, parent=None):
        super().__init__(parent)
        self.setWindowTitle("End Session")
        self.setGeometry(100, 100, 400, 300)
        self.apps = apps
        self.hourly_wage = hourly_wage

        layout = QVBoxLayout(self)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Application", "Window", "Time Spent", "Select"])
        self.tree_widget.header().setStyleSheet("QHeaderView::section { background-color: #444444; color: #ffffff; }")
        layout.addWidget(self.tree_widget)

        self.populate_tree()

        self.total_label = QLabel("Total Wage: $0.00")
        layout.addWidget(self.total_label)

        self.hourly_wage_label = QLabel("Hourly Wage ($):")
        layout.addWidget(self.hourly_wage_label)

        self.hourly_wage_edit = QSpinBox()
        self.hourly_wage_edit.setRange(1, 1000)
        self.hourly_wage_edit.setValue(self.hourly_wage)
        self.hourly_wage_edit.valueChanged.connect(self.calculate_total_wage)
        layout.addWidget(self.hourly_wage_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.tree_widget.itemChanged.connect(self.handle_item_changed)

        logging.info("EndSessionDialog initialized.")

    def populate_tree(self):
        try:
            for category, app_times in self.apps.items():
                for app, window_times in app_times.items():
                    app_item = QTreeWidgetItem([app])
                    app_item.setCheckState(3, Qt.Unchecked)
                    self.tree_widget.addTopLevelItem(app_item)
                    for window, time_spent in window_times.items():
                        formatted_time = self.format_time(time_spent)
                        window_item = QTreeWidgetItem([app, window, formatted_time])
                        window_item.setCheckState(3, Qt.Unchecked)
                        app_item.addChild(window_item)
            self.tree_widget.expandAll()
            logging.debug("Tree populated in EndSessionDialog.")
        except Exception as e:
            logging.error(f"Error populating tree in EndSessionDialog: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while populating the tree: {e}")

    def format_time(self, seconds):
        try:
            hours, remainder = divmod(seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        except Exception as e:
            logging.error(f"Error formatting time in EndSessionDialog: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while formatting the time: {e}")
            return "0h 0m 0s"

    def handle_item_changed(self, item, column):
        try:
            if column == 3:
                state = item.checkState(column)
                for i in range(item.childCount()):
                    child = item.child(i)
                    child.setCheckState(column, state)
                self.calculate_total_wage()
            logging.debug("Item state changed in EndSessionDialog.")
        except Exception as e:
            logging.error(f"Error handling item change in EndSessionDialog: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while handling item change: {e}")

    def calculate_total_wage(self):
        try:
            total_seconds = 0
            for i in range(self.tree_widget.topLevelItemCount()):
                app_item = self.tree_widget.topLevelItem(i)
                if app_item.checkState(3) == Qt.Checked:
                    for j in range(app_item.childCount()):
                        window_item = app_item.child(j)
                        time_text = window_item.text(2)
                        hours, minutes, seconds = map(int, time_text.replace("h", "").replace("m", "").replace("s", "").split())
                        total_seconds += hours * 3600 + minutes * 60 + seconds
                else:
                    for j in range(app_item.childCount()):
                        window_item = app_item.child(j)
                        if window_item.checkState(3) == Qt.Checked:
                            time_text = window_item.text(2)
                            hours, minutes, seconds = map(int, time_text.replace("h", "").replace("m", "").replace("s", "").split())
                            total_seconds += hours * 3600 + minutes * 60 + seconds
            hourly_wage = self.hourly_wage_edit.value()
            total_wage = (total_seconds / 3600) * hourly_wage
            self.total_label.setText(f"Total Wage: ${total_wage:.2f}")
            logging.debug("Total wage calculated in EndSessionDialog.")
        except Exception as e:
            logging.error(f"Error calculating total wage in EndSessionDialog: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while calculating the total wage: {e}")
