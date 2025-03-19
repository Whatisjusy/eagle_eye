import pytest
import psutil
from unittest.mock import patch, MagicMock
from utils.app_tracker_utils import AppTrackerUtilities, get_app_cpu_usage, save_session_data, load_session_data

@pytest.fixture
def app_tracker_utils():
    return AppTrackerUtilities()

def test_get_active_app(app_tracker_utils):
    with patch('win32gui.GetForegroundWindow', return_value=1234), \
         patch('win32process.GetWindowThreadProcessId', return_value=(None, 5678)), \
         patch('win32gui.GetWindowText', return_value="Test Window"), \
         patch('psutil.process_iter', return_value=[MagicMock(info={'pid': 5678, 'name': 'test.exe'})]):
        app_name, pid, window_title = app_tracker_utils.get_active_app()
        assert app_name == "test.exe"
        assert pid == 5678
        assert window_title == "Test Window"

def test_get_active_app_no_window(app_tracker_utils):
    with patch('win32gui.GetForegroundWindow', return_value=None):
        app_name, pid, window_title = app_tracker_utils.get_active_app()
        assert app_name is None
        assert pid is None
        assert window_title is None

def test_get_app_name(app_tracker_utils):
    with patch.object(app_tracker_utils, 'get_app_name_from_executable', return_value="test_app"):
        app_name = app_tracker_utils.get_app_name(1234)
        assert app_name == "test_app"
        assert app_tracker_utils.app_name_cache[1234] == "test_app"

def test_get_app_name_from_executable(app_tracker_utils):
    with patch('psutil.Process') as mock_process:
        mock_process.return_value.exe.return_value = "C:\\path\\to\\test_app.exe"
        with patch('win32api.GetFileVersionInfo', return_value={'FileDescription': 'Test App'}):
            app_name = app_tracker_utils.get_app_name_from_executable(1234)
            assert app_name == "Test App"

def test_update_baseline(app_tracker_utils):
    pid = 1234
    cpu, mem, io = 10, 20, 30
    avg_cpu, avg_mem, avg_io = app_tracker_utils.update_baseline(pid, cpu, mem, io)
    assert avg_cpu == 10
    assert avg_mem == 20
    assert avg_io == 30

def test_categorize_activity(app_tracker_utils):
    window_title = "Test Window"
    with patch('utils.app_tracker_utils.activity_categories', {'test': ['Test']}):
        category = app_tracker_utils.categorize_activity(window_title)
        assert category == "test"

def test_get_app_cpu_usage():
    with patch('psutil.Process') as mock_process:
        mock_process.return_value.cpu_percent.return_value = 10.0
        mock_process.return_value.memory_percent.return_value = 20.0
        mock_process.return_value.io_counters.return_value = MagicMock(read_bytes=1000, write_bytes=2000)
        cpu, mem, io = get_app_cpu_usage(1234)
        assert cpu == 10.0
        assert mem == 20.0
        assert io == 3000

def test_save_session_data(app_tracker_utils):
    app_tracker_utils.active_apps = {"test": "data"}
    with patch('builtins.open', new_callable=MagicMock) as mock_open:
        save_session_data()
        mock_open.assert_called_once_with("history.json", "w", encoding="utf-8", errors="ignore")

def test_load_session_data():
    with patch('os.path.exists', return_value=True), \
         patch('builtins.open', new_callable=MagicMock) as mock_open, \
         patch('json.load', return_value={"test": "data"}):
        data = load_session_data()
        assert data == {"test": "data"}

def test_load_session_data_no_file():
    with patch('os.path.exists', return_value=False):
        data = load_session_data()
        assert data == {}
