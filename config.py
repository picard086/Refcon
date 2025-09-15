import sqlite3

DB_PATH = "economy.db"

def load_server_config():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM servers LIMIT 1")
    row = cur.fetchone()
    if not row:
        raise RuntimeError("No server configured in database. Run install.sh again.")
    return dict(row)
