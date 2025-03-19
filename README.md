# Eagle Eye

## Project Description

Eagle Eye is a tool designed to monitor and track the active applications on your system. It provides detailed information about the time spent on each application and window, helping you analyze your productivity and usage patterns.

## Installation

### Dependencies

Ensure you have the following dependencies installed:

- Python 3.6+
- PyQt5
- psutil
- pynput
- win32api
- win32gui
- win32process

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Whatisjusy/eagle_eye.git
   cd eagle_eye
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Application

To start Eagle Eye, run the following command:
```bash
python -m eagle_eye
```

### UI Walkthrough

- **Live Tracking Tab**: Displays the active applications and windows being tracked in real-time.
- **Debug Log Tab**: Shows the debug log for troubleshooting and monitoring.
- **Settings Tab**: Allows you to configure the inactivity timeout, CPU usage threshold, and hourly wage.

### Example Commands

- **Reset Progress**: Click the "Reset Progress" button to reset the tracking data.
- **End Session**: Click the "End Session" button to end the current session and calculate the total wage.

## Project Structure

```
eagle-eye/
├── gui.py                # GUI components and main application window
├── utils/
│   ├── app_tracker_utils.py  # Utility functions for tracking applications
│   ├── config.py             # Configuration settings and constants
├── tests/
│   ├── test_app_tracker_utils.py  # Unit tests for app_tracker_utils.py
│   ├── test_gui.py                # Unit tests for gui.py
├── .pylintrc              # Pylint configuration file
├── .flake8                # Flake8 configuration file
├── .gitignore             # Git ignore file
├── CONTRIBUTING.md        # Contribution guidelines
├── README.md              # Project documentation
```

## Contribution Guidelines

We welcome contributions! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## Author

- Your Name (your-email@example.com)

Thank you for using Eagle Eye!
