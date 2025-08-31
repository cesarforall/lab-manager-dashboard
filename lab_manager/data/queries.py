import sqlite3

def get_manufacturers(conn):
    c = conn.cursor()
    c.execute("SELECT DISTINCT manufacturer FROM Devices ORDER BY manufacturer")
    return [row[0] for row in c.fetchall()]

def get_models_by_manufacturer(conn, manufacturer=None):
    c = conn.cursor()
    if manufacturer is None or manufacturer == "Todas":
        c.execute("SELECT DISTINCT model FROM Devices")
    else:
        c.execute("SELECT DISTINCT model FROM Devices WHERE manufacturer=?", (manufacturer,))
    return [row[0] for row in c.fetchall()]

def get_all_technicians(conn):
    c = conn.cursor()
    c.execute("SELECT id, name, created_at FROM Technicians;")
    return c.fetchall()

def get_total_technicians(conn):
    c = conn.cursor()
    c.execute("""
        SELECT COUNT(DISTINCT technician_id)
        FROM Assignments
        WHERE technician_id IS NOT NULL
    """)
    return c.fetchone()[0]

def get_workstations_with_assignments(conn):
    c = conn.cursor()
    c.execute("""
        SELECT w.id, t.id, w.name, t.name, w.pos_x, w.pos_y, p.serial_number
        FROM Workstations w
        LEFT JOIN Assignments a ON w.id = a.workstation_id
        LEFT JOIN Technicians t ON a.technician_id = t.id
        LEFT JOIN PCs p ON a.pc_id = p.id
    """)
    return c.fetchall()

def get_technician_devices(conn, tech_id):
    """Devuelve los dispositivos en los que el técnico tiene formación"""
    c = conn.cursor()
    c.execute("""
        SELECT d.manufacturer, d.model
        FROM Trainings tr
        JOIN Devices d ON tr.device_id = d.id
        WHERE tr.technician_id = ?
    """, (tech_id,))
    return c.fetchall()

def get_pending_updates_count(conn, tech_id, manufacturer=None, models=None):
    sql = """
        SELECT COUNT(*)
        FROM Trainings tr
        JOIN DeviceUpdates du ON tr.device_id = du.device_id
        LEFT JOIN TechnicianUpdateConfirmations tuc
            ON tuc.technician_id = tr.technician_id AND tuc.update_id = du.id
        JOIN Devices d ON tr.device_id = d.id
        WHERE tr.technician_id = ? AND COALESCE(tuc.confirmed,0)=0
    """
    params = [tech_id]
    conditions = []
    if manufacturer and manufacturer != "Todas":
        conditions.append("d.manufacturer = ?")
        params.append(manufacturer)
    if models:
        placeholders = ",".join("?"*len(models))
        conditions.append(f"d.model IN ({placeholders})")
        params.extend(models)
    if conditions:
        sql += " AND " + " AND ".join(conditions)

    c = conn.cursor()
    c.execute(sql, params)
    return c.fetchone()[0]

def get_updates_for_technician(conn, tech_id):
    c = conn.cursor()
    c.execute("""
        SELECT d.manufacturer, d.model, du.version,
            COALESCE(tuc.confirmed, 0) AS confirmed, du.id AS update_id
        FROM Trainings tr
        JOIN Devices d ON tr.device_id = d.id
        LEFT JOIN DeviceUpdates du ON d.id = du.device_id
        LEFT JOIN TechnicianUpdateConfirmations tuc
            ON tuc.technician_id = tr.technician_id AND tuc.update_id = du.id
        WHERE tr.technician_id = ?
        ORDER BY du.id DESC
    """, (tech_id,))
    return c.fetchall()

def get_latest_updates_for_technician(conn, tech_id, limit_per_model=2):
    c = conn.cursor()
    c.execute(f"""
        SELECT manufacturer, model, version, confirmed, update_id FROM (
            SELECT d.manufacturer, d.model, du.version,
                   COALESCE(tuc.confirmed, 0) AS confirmed,
                   du.id AS update_id,
                   ROW_NUMBER() OVER(PARTITION BY d.id ORDER BY du.id DESC) AS rn
            FROM Trainings t
            JOIN Devices d ON t.device_id = d.id
            LEFT JOIN DeviceUpdates du ON d.id = du.device_id
            LEFT JOIN TechnicianUpdateConfirmations tuc
                ON tuc.technician_id = t.technician_id AND tuc.update_id = du.id
            WHERE t.technician_id = ?
        ) WHERE rn <= ?
    """, (tech_id, limit_per_model))
    return c.fetchall()

def get_latest_device_updates(conn, limit=20):
    c = conn.cursor()
    c.execute("""
        SELECT d.manufacturer, d.model, du.version, du.created_at
        FROM DeviceUpdates du
        JOIN Devices d ON du.device_id = d.id
        ORDER BY du.created_at DESC
        LIMIT ?
    """, (limit,))
    return c.fetchall()

def mark_update_as_confirmed(conn, technician_id, update_id):
    c = conn.cursor()
    c.execute(
        "UPDATE TechnicianUpdateConfirmations SET confirmed=1 WHERE technician_id=? AND update_id=?",
        (technician_id, update_id)
    )
    conn.commit()

def get_technician_trainings(conn, tech_id):
    """
    Devuelve una lista de dispositivos en los que el técnico tiene formaciones.
    Cada elemento es (manufacturer, model, training_type, trainer_name, competency_level).
    """
    c = conn.cursor()
    c.execute("""
        SELECT d.manufacturer, d.model, t.training_type, t.trainer_name, t.competency_level
        FROM Trainings t
        JOIN Devices d ON t.device_id = d.id
        WHERE t.technician_id = ?
    """, (tech_id,))
    return c.fetchall()

def add_device_update(conn, manufacturer, model, version):
    c = conn.cursor()
    c.execute(
        "SELECT id FROM Devices WHERE manufacturer=? AND model=?",
        (manufacturer, model)
    )
    row = c.fetchone()
    if not row:
        raise ValueError(f"Dispositivo no encontrado: {manufacturer} {model}")

    device_id = row[0]

    c.execute(
        "SELECT 1 FROM DeviceUpdates WHERE device_id=? AND version=?",
        (device_id, version)
    )
    if c.fetchone():
        return False

    c.execute(
        "INSERT INTO DeviceUpdates (device_id, version) VALUES (?, ?)",
        (device_id, version)
    )
    conn.commit()
    return True
