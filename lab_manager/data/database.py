import sqlite3
from pathlib import Path

DB_FILE = "lab_manager.db"

def get_connection(db_path: str = DB_FILE) -> sqlite3.Connection:
    """Abre y devuelve una conexión a la base de datos SQLite."""
    conn = sqlite3.connect(db_path)
    return conn

def init_db(db_path: str = DB_FILE):
    """Inicializa la base de datos si no existe."""
    if not Path(db_path).exists():
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS Devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            manufacturer TEXT NOT NULL,
            model TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS Technicians (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS Workstations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            pos_x INTEGER NOT NULL,
            pos_y INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS PCs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER NOT NULL,
            serial_number TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(device_id) REFERENCES Devices(id)
        );

        CREATE TABLE IF NOT EXISTS Assignments (
            workstation_id INTEGER NOT NULL UNIQUE,
            technician_id INTEGER NOT NULL UNIQUE,
            pc_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (workstation_id, technician_id),
            FOREIGN KEY(workstation_id) REFERENCES Workstations(id),
            FOREIGN KEY(technician_id) REFERENCES Technicians(id),
            FOREIGN KEY(pc_id) REFERENCES PCs(id)
        );

        CREATE TABLE IF NOT EXISTS TechnicianDevices (
            technician_id INTEGER NOT NULL,
            device_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(technician_id) REFERENCES Technicians(id),
            FOREIGN KEY(device_id) REFERENCES Devices(id)
        );

        CREATE TABLE IF NOT EXISTS DeviceUpdates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER NOT NULL,
            version TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(device_id) REFERENCES Devices(id)
        );

        CREATE TABLE IF NOT EXISTS TechnicianUpdateConfirmations (
            technician_id INTEGER NOT NULL,
            update_id INTEGER NOT NULL,
            confirmed INTEGER NOT NULL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (technician_id, update_id),
            FOREIGN KEY(technician_id) REFERENCES Technicians(id),
            FOREIGN KEY(update_id) REFERENCES DeviceUpdates(id)
        );
        """)
        conn.commit()
        conn.close()
