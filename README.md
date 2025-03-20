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
- pywin32

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/eagle-eye.git
   cd eagle-eye
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
python src/main.py
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
├── src/
│   ├── app_tracker_utils.py  # Utility functions for tracking applications
│   ├── config.py             # Configuration settings and constants
│   ├── gui.py                # GUI components and main application window
│   ├── main.py               # Main script to run the application
│   ├── tracker_thread.py     # Thread for tracking applications
├── tests/
│   ├── test_app_tracker_utils.py  # Unit tests for app_tracker_utils.py
│   ├── test_gui.py                # Unit tests for gui.py
├── .pylintrc.ini            # Pylint configuration file
├── .flake8.ini              # Flake8 configuration file
├── .gitignore               # Git ignore file
├── README.md                # Project documentation
├── requirements.txt         # Project dependencies
```

## Contribution Guidelines

We welcome contributions! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Code of Conduct

We as members, contributors, and leaders pledge to make participation in our community a harassment-free experience for everyone, regardless of age, body size, visible or invisible disability, ethnicity, sex characteristics, gender identity and expression, level of experience, education, socio-economic status, nationality, personal appearance, race, religion, or sexual identity and orientation.

We pledge to act and interact in ways that contribute to an open, welcoming, diverse, inclusive, and healthy community.

## Author

- Your Name (your-email@example.com)

Thank you for using Eagle Eye!
