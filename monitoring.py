import os
import time
import sqlite3
import psutil
import subprocess
from multiprocessing import Process

# Constants
PERSISTENCE_DB = "persistence_data.db"
LOG_FILE = "persistence.log"
CHECK_INTERVAL = 30  # Time in seconds between checks

# Initialize SQLite database
conn = sqlite3.connect(PERSISTENCE_DB)
cursor = conn.cursor()

# Create necessary tables
cursor.execute('''CREATE TABLE IF NOT EXISTS system_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    passwd TEXT,
                    shadow TEXT,
                    group_file TEXT,
                    open_ports TEXT,
                    autostart_services TEXT,
                    security_logs TEXT,
                    recent_files TEXT,
                    process_info TEXT)''')
conn.commit()


def log_event(message):
    """Log events to the log file."""
    with open(LOG_FILE, "a") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")


def get_file_content(path):
    """Read and return file content."""
    try:
        with open(path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        return ""


def get_open_ports():
    """Get a list of open network ports."""
    try:
        result = subprocess.run(['netstat', '-tuln'], capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        log_event(f"Error getting open ports: {e}")
        return ""


def get_autostart_services():
    """Get a list of services set to autostart."""
    try:
        result = subprocess.run(['systemctl', 'list-unit-files', '--type=service', '--state=enabled'],
                                capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        log_event(f"Error getting autostart services: {e}")
        return ""


def get_security_logs():
    """Get contents of security logs."""
    log_paths = ["/var/log/auth.log", "/var/log/secure", "/var/log/wtmp", "/var/log/btmp"]
    logs = {}
    for log in log_paths:
        logs[log] = get_file_content(log)
    return str(logs)


def get_recently_modified_files():
    """Find recently modified files in the last 2 days."""
    try:
        result = subprocess.run(['find', '/', '-mtime', '-2', '-ls'], capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        log_event(f"Error getting recently modified files: {e}")
        return ""


def get_process_info():
    """Get information about running processes."""
    try:
        result = subprocess.run(['ps', 'auxwf'], capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        log_event(f"Error getting process information: {e}")
        return ""


def take_snapshot():
    """Take a snapshot of system files and states."""
    passwd_content = get_file_content('/etc/passwd')
    shadow_content = get_file_content('/etc/shadow')
    group_content = get_file_content('/etc/group')
    open_ports = get_open_ports()
    autostart_services = get_autostart_services()
    security_logs = get_security_logs()
    recent_files = get_recently_modified_files()
    process_info = get_process_info()

    cursor.execute('''INSERT INTO system_snapshots (passwd, shadow, group_file, open_ports, autostart_services,
                      security_logs, recent_files, process_info)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                   (passwd_content, shadow_content, group_content, open_ports, autostart_services,
                    security_logs, recent_files, process_info))
    conn.commit()

    log_event("System snapshot taken.")


def detect_changes():
    """Compare the latest two snapshots and log any differences."""
    cursor.execute('''SELECT * FROM system_snapshots ORDER BY id DESC LIMIT 2''')
    snapshots = cursor.fetchall()

    if len(snapshots) < 2:
        return

    latest, previous = snapshots[0], snapshots[1]
    differences = []

    if latest[2] != previous[2]:
        differences.append("Changes detected in /etc/passwd.")
    if latest[3] != previous[3]:
        differences.append("Changes detected in /etc/shadow.")
    if latest[4] != previous[4]:
        differences.append("Changes detected in /etc/group.")
    if latest[5] != previous[5]:
        differences.append("Changes detected in open ports.")
    if latest[6] != previous[6]:
        differences.append("Changes detected in autostart services.")
    if latest[7] != previous[7]:
        differences.append("Changes detected in security logs.")
    if latest[8] != previous[8]:
        differences.append("Changes detected in recently modified files.")
    if latest[9] != previous[9]:
        differences.append("Changes detected in running processes.")

    for difference in differences:
        log_event(difference)


def run_daemon():
    """Main daemon loop."""
    log_event("Security daemon started.")
    while True:
        take_snapshot()
        detect_changes()
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    # Run as a background process
    daemon_process = Process(target=run_daemon)
    daemon_process.daemon = True
    daemon_process.start()
    log_event("Daemon process started successfully.")

    # Keep the main program alive
    while True:
        time.sleep(1)
