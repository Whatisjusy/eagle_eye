import pytest
import psutil
from unittest.mock import patch, MagicMock
from src.app_tracker_utils import AppTrackerUtilities, get_app_cpu_usage, save_session_data, load_session_data, get_app_memory_usage

@pytest.fixture
def app_tracker_utils():
    return AppTrackerUtilities()

# ...existing code...

def test_get_app_memory_usage():
    with patch('psutil.Process') as mock_process:
        mock_process.return_value.memory_info.return_value = MagicMock(rss=1000, vms=2000)
        rss, vms = get_app_memory_usage(1234)
        assert rss == 1000
        assert vms == 2000

# Add more tests for other critical functions
def test_load_session_data():
    with patch('os.path.exists', return_value=True), \
         patch('builtins.open', new_callable=MagicMock) as mock_open, \
         patch('json.load', return_value={"test": "data"}):
        data = load_session_data()
        assert data == {"test": "data"}

def test_save_session_data(app_tracker_utils):
    app_tracker_utils.active_apps = {"test": "data"}
    with patch('builtins.open', new_callable=MagicMock) as mock_open:
        save_session_data()
        mock_open.assert_called_once_with("history.json", "w", encoding="utf-8", errors="ignore")
