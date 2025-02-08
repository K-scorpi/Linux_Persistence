import os
import time
import json
import sqlite3
import logging
from datetime import datetime
from abc import ABC, abstractmethod

# Paths and settings
LOG_FILE = "/var/log/persistence.log"
DB_FILE = "persistence_monitor.db"
SCAN_INTERVAL = 60  # in seconds

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='[%(asctime)s] %(message)s'
)

# Database setup
def initialize_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            module TEXT,
            snapshot_data TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diffs (
            id INTEGER PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            module TEXT,
            differences TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Base class for persistence monitoring modules
class PersistenceModuleBase(ABC):

    @abstractmethod
    def take_snapshot(self) -> dict:
        pass

    @abstractmethod
    def compare_snapshot(self, previous_snapshot: dict) -> list:
        pass

    def log_differences(self, differences: list):
        if differences:
            message = f"{self.__class__.__name__}: {differences}"
            logging.info(message)
            self.save_differences_to_db(differences)

    def save_snapshot_to_db(self, snapshot_data: dict):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO snapshots (module, snapshot_data) VALUES (?, ?)",
            (self.__class__.__name__, json.dumps(snapshot_data))
        )
        conn.commit()
        conn.close()

    def save_differences_to_db(self, differences: list):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO diffs (module, differences) VALUES (?, ?)",
            (self.__class__.__name__, json.dumps(differences))
        )
        conn.commit()
        conn.close()

class PasswdMonitor(PersistenceModuleBase):

    PASSWD_FILE = "/etc/passwd"

    def take_snapshot(self) -> dict:
        try:
            with open(self.PASSWD_FILE, 'r') as f:
                return {"content": f.read()}
        except Exception as e:
            logging.error(f"Error reading {self.PASSWD_FILE}: {e}")
            return {}

    def compare_snapshot(self, previous_snapshot: dict) -> list:
        current_snapshot = self.take_snapshot()
        if not current_snapshot or not previous_snapshot:
            return []

        if current_snapshot["content"] != previous_snapshot.get("content"):
            return ["/etc/passwd content changed"]
        return []

class PersistenceMonitorService:

    def __init__(self, modules):
        self.modules = modules

    def load_last_snapshot(self, module_name: str) -> dict:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT snapshot_data FROM snapshots WHERE module = ? ORDER BY timestamp DESC LIMIT 1",
            (module_name,)
        )
        row = cursor.fetchone()
        conn.close()
        return json.loads(row[0]) if row else {}

    def run(self):
        logging.info("Persistence Monitor Service started.")
        while True:
            for module in self.modules:
                previous_snapshot = self.load_last_snapshot(module.__class__.__name__)
                current_snapshot = module.take_snapshot()
                module.save_snapshot_to_db(current_snapshot)

                differences = module.compare_snapshot(previous_snapshot)
                module.log_differences(differences)

            time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    initialize_database()

    # Register monitoring modules
    modules = [
        PasswdMonitor(),
    ]

    service = PersistenceMonitorService(modules)
    service.run()
