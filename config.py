import os
import sqlite3

# Always resolve DB path relative to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "economy.db")


def load_server_config():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, ip, port, password FROM servers LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise RuntimeError("No server configured in database. Run install.sh again.")

    return {
        "id": row[0],
        "name": row[1],
        "ip": row[2],
        "port": row[3],
        "password": row[4],
    }
