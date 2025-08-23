import sqlite3
import random

conn = sqlite3.connect('lab_manager.db')
c = conn.cursor()

c.executescript("""
DROP TABLE IF EXISTS Workstations;
DROP TABLE IF EXISTS Technicians;
DROP TABLE IF EXISTS Devices;
DROP TABLE IF EXISTS PCs;
DROP TABLE IF EXISTS Assignments;
DROP TABLE IF EXISTS TechnicianDevices;
DROP TABLE IF EXISTS DeviceUpdates;
DROP TABLE IF EXISTS TechnicianUpdateConfirmations;

CREATE TABLE Workstations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    pos_x INTEGER NOT NULL,
    pos_y INTEGER NOT NULL
);

CREATE TABLE Technicians (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE Devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manufacturer TEXT NOT NULL,
    model TEXT NOT NULL
);

CREATE TABLE PCs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    serial_number TEXT NOT NULL,
    FOREIGN KEY(device_id) REFERENCES Devices(id)
);

CREATE TABLE Assignments (
    workstation_id INTEGER NOT NULL UNIQUE,
    technician_id INTEGER NOT NULL UNIQUE,
    pc_id INTEGER NOT NULL,
    PRIMARY KEY (workstation_id, technician_id),
    FOREIGN KEY(workstation_id) REFERENCES Workstations(id),
    FOREIGN KEY(technician_id) REFERENCES Technicians(id),
    FOREIGN KEY(pc_id) REFERENCES PCs(id)
);

CREATE TABLE TechnicianDevices (
    technician_id INTEGER NOT NULL,
    device_id INTEGER NOT NULL,
    FOREIGN KEY(technician_id) REFERENCES Technicians(id),
    FOREIGN KEY(device_id) REFERENCES Devices(id)
);

CREATE TABLE DeviceUpdates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    version TEXT NOT NULL,
    FOREIGN KEY(device_id) REFERENCES Devices(id)
);

CREATE TABLE TechnicianUpdateConfirmations (
    technician_id INTEGER NOT NULL,
    update_id INTEGER NOT NULL,
    confirmed INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (technician_id, update_id),
    FOREIGN KEY(technician_id) REFERENCES Technicians(id),
    FOREIGN KEY(update_id) REFERENCES DeviceUpdates(id)
);
""")

max_cols = 10
max_rows = 6

# Crear WS en posiciones fijas
workstations = []
for row in range(max_rows):
    for col in range(max_cols):
        ws_name = f"WS_{row}_{col}"
        workstations.append((ws_name, col, row))
c.executemany("INSERT INTO Workstations (name, pos_x, pos_y) VALUES (?,?,?)", workstations)

# Technicians
technicians = [
    "Ana García", "Luis Martínez", "Marta López", "Carlos Sánchez", "Laura Fernández",
    "David Rodríguez", "Elena Gómez", "Javier Ruiz", "Sofía Díaz", "Pablo Moreno",
    "Isabel Jiménez", "Miguel Torres", "Carmen Ortega", "Alberto Molina", "Lucía Castillo",
    "Fernando Ramos", "María Alonso", "José Vázquez", "Patricia Herrera", "Antonio Delgado"
]
c.executemany("INSERT INTO Technicians (name) VALUES (?)", [(t,) for t in technicians])

# Devices (nuevos fabricantes y modelos)
manufacturers_models = [
    ("Apple", "MacBook Pro"), ("HP", "Spectre x360"), ("Dell", "XPS 15"),
    ("Lenovo", "ThinkBook"), ("Asus", "ZenBook 14"), ("Acer", "Swift 3"),
    ("MSI", "Prestige 15")
]
c.executemany("INSERT INTO Devices (manufacturer, model) VALUES (?,?)", manufacturers_models)

# PCs
pcs = [(i % len(manufacturers_models) + 1, f"PC_{i:03}") for i in range(1, max_cols*max_rows+1)]
c.executemany("INSERT INTO PCs (device_id, serial_number) VALUES (?,?)", pcs)

# Assignments: uno a uno
ws_ids = list(range(1, max_cols*max_rows+1))
tech_ids = list(range(1, len(technicians)+1))
random.shuffle(ws_ids)
random.shuffle(tech_ids)

assignments = []
for tech_id, ws_id in zip(tech_ids, ws_ids):
    pc_id = ws_id
    assignments.append((ws_id, tech_id, pc_id))

c.executemany("INSERT INTO Assignments (workstation_id, technician_id, pc_id) VALUES (?,?,?)", assignments)

# TechnicianDevices
td = []
for tech_id in tech_ids:
    devices_for_tech = random.sample(range(1, len(manufacturers_models)+1), random.randint(1, 4))
    for device_id in devices_for_tech:
        td.append((tech_id, device_id))
c.executemany("INSERT INTO TechnicianDevices (technician_id, device_id) VALUES (?,?)", td)

# DeviceUpdates
du = []
for device_id in range(1, len(manufacturers_models)+1):
    for v in range(1, random.randint(2,4)):
        du.append((device_id, f"v{v}.0"))
c.executemany("INSERT INTO DeviceUpdates (device_id, version) VALUES (?,?)", du)

# TechnicianUpdateConfirmations
tuc = []
for tech_id in tech_ids:
    for device_id in range(1, len(manufacturers_models)+1):
        c.execute("SELECT id FROM DeviceUpdates WHERE device_id=?", (device_id,))
        updates = [row[0] for row in c.fetchall()]
        for upd_id in updates:
            confirmed = random.choice([0,0,0,1])
            tuc.append((tech_id, upd_id, confirmed))
c.executemany("INSERT INTO TechnicianUpdateConfirmations (technician_id, update_id, confirmed) VALUES (?,?,?)", tuc)

conn.commit()
conn.close()
