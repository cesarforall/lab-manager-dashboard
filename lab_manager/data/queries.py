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
    c = conn.cursor()
    c.execute("""
        SELECT d.manufacturer, d.model
        FROM TechnicianDevices td
        JOIN Devices d ON td.device_id = d.id
        WHERE td.technician_id = ?
    """, (tech_id,))
    return c.fetchall()

def get_pending_updates_count(conn, tech_id, manufacturer=None, models=None):
    sql = """
        SELECT COUNT(*)
        FROM TechnicianDevices td
        JOIN DeviceUpdates du ON td.device_id = du.device_id
        LEFT JOIN TechnicianUpdateConfirmations tuc
            ON tuc.technician_id = td.technician_id AND tuc.update_id = du.id
        JOIN Devices d ON td.device_id = d.id
        WHERE td.technician_id = ? AND COALESCE(tuc.confirmed,0)=0
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
        FROM TechnicianDevices td
        JOIN Devices d ON td.device_id = d.id
        LEFT JOIN DeviceUpdates du ON d.id = du.device_id
        LEFT JOIN TechnicianUpdateConfirmations tuc
            ON tuc.technician_id = td.technician_id AND tuc.update_id = du.id
        WHERE td.technician_id = ?
        ORDER BY du.id DESC
    """, (tech_id,))
    return c.fetchall()
    
def get_latest_updates_for_technician(conn, tech_id):
    c = conn.cursor()
    c.execute("""
        SELECT manufacturer, model, version, confirmed, update_id
        FROM (
            SELECT d.manufacturer, d.model, du.version,
                COALESCE(tuc.confirmed, 0) AS confirmed,
                du.id AS update_id
            FROM TechnicianDevices td
            JOIN Devices d ON td.device_id = d.id
            LEFT JOIN DeviceUpdates du ON d.id = du.device_id
            LEFT JOIN TechnicianUpdateConfirmations tuc
                ON tuc.technician_id = td.technician_id AND tuc.update_id = du.id
            WHERE td.technician_id = ?
            ORDER BY du.id DESC
        )
        GROUP BY manufacturer, model
    """, (tech_id,))
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
