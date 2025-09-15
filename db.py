import sqlite3

DB_PATH = "economy.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- Players ----------------
def get_player(conn, eos, server_id, name=None):
    cur = conn.execute("SELECT * FROM players WHERE eos=? AND server_id=?", (eos, server_id))
    row = cur.fetchone()
    if not row:
        conn.execute(
            "INSERT INTO players (server_id, eos, name) VALUES (?, ?, ?)",
            (server_id, eos, name or eos)
        )
        conn.commit()
        return get_player(conn, eos, server_id, name)
    return dict(row)

def update_balance(conn, eos, server_id, coins=None, gold=None):
    if coins is not None:
        conn.execute("UPDATE players SET coins=? WHERE eos=? AND server_id=?", (coins, eos, server_id))
    if gold is not None:
        conn.execute("UPDATE players SET gold=? WHERE eos=? AND server_id=?", (gold, eos, server_id))
    conn.commit()

def update_field(conn, eos, server_id, field, value):
    conn.execute(f"UPDATE players SET {field}=? WHERE eos=? AND server_id=?", (value, eos, server_id))
    conn.commit()

# ---------------- Teleports ----------------
def add_teleport(conn, player_id, name, pos):
    conn.execute(
        "INSERT INTO teleports (player_id, name, x, y, z) VALUES (?, ?, ?, ?, ?)",
        (player_id, name, pos[0], pos[1], pos[2])
    )
    conn.commit()

def get_teleports(conn, player_id):
    cur = conn.execute("SELECT * FROM teleports WHERE player_id=?", (player_id,))
    return [dict(row) for row in cur.fetchall()]

def del_teleport(conn, player_id, name):
    conn.execute("DELETE FROM teleports WHERE player_id=? AND name=?", (player_id, name))
    conn.commit()

# ---------------- Shops ----------------
def get_shop(conn, shop_type):
    cur = conn.execute("SELECT * FROM shops WHERE type=?", (shop_type,))
    return [dict(row) for row in cur.fetchall()]

# ---------------- Admins ----------------
def is_admin(conn, eos):
    cur = conn.execute("SELECT eos FROM admins WHERE eos=?", (eos,))
    return cur.fetchone() is not None

def add_admin(conn, eos):
    conn.execute("INSERT OR IGNORE INTO admins (eos) VALUES (?)", (eos,))
    conn.commit()

# ---------------- Votes ----------------
def get_vote(conn, eos):
    cur = conn.execute("SELECT * FROM votes WHERE eos=?", (eos,))
    return cur.fetchone()

def save_vote(conn, eos, ts):
    conn.execute("INSERT OR REPLACE INTO votes (eos, last_vote) VALUES (?, ?)", (eos, ts))
    conn.commit()
