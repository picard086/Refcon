import sqlite3

DB_PATH = "economy.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    return conn


# ---------------- Schema ----------------
def ensure_schema(conn):
    """Ensure all required tables exist."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id TEXT,
            eos TEXT,
            steam TEXT,
            name TEXT,
            coins INTEGER DEFAULT 0,
            gold INTEGER DEFAULT 0,
            multiplier REAL DEFAULT 1.0,
            donor TEXT DEFAULT NULL,
            starter_used INTEGER DEFAULT 0,
            last_daily INTEGER DEFAULT 0,
            last_gimme INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS teleports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            name TEXT,
            x REAL,
            y REAL,
            z REAL
        );

        CREATE TABLE IF NOT EXISTS admins (
            eos TEXT PRIMARY KEY
        );

        CREATE TABLE IF NOT EXISTS votes (
            eos TEXT PRIMARY KEY,
            last_vote INTEGER
        );

        CREATE TABLE IF NOT EXISTS shops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            name TEXT,
            friendly TEXT,
            price INTEGER,
            amount INTEGER
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """
    )
    # add steam column if missing
    try:
        conn.execute("ALTER TABLE players ADD COLUMN steam TEXT;")
    except sqlite3.OperationalError:
        pass
    conn.commit()


# ---------------- Players ----------------
def get_player(conn, eos, server_id, name=None, steam=None):
    # Special handling for WebAdmin (API bridge user)
    if eos == "WebAdmin":
        conn.execute(
            """
            INSERT OR IGNORE INTO players (server_id, eos, steam, name, coins, gold, multiplier, donor,
                                           starter_used, last_daily, last_gimme, streak)
            VALUES (?, 'WebAdmin', 'WebAdmin', 'WebAdmin', 0, 0, 1.0, NULL, 0, 0, 0, 0)
            """,
            (server_id,),
        )
        conn.commit()

    # 🚩 Always prefer STEAM as the canonical identifier
    if steam:
        cur = conn.execute(
            "SELECT * FROM players WHERE steam=? AND server_id=?", (steam, server_id)
        )
        row = cur.fetchone()
    else:
        cur = conn.execute(
            "SELECT * FROM players WHERE eos=? AND server_id=?", (eos, server_id)
        )
        row = cur.fetchone()

    if row:
        # Update stored EOS if missing or outdated
        if eos and (not row["eos"] or row["eos"] != eos):
            conn.execute("UPDATE players SET eos=? WHERE id=?", (eos, row["id"]))
        conn.commit()
        cur = conn.execute("SELECT * FROM players WHERE id=?", (row["id"],))
        return dict(cur.fetchone())

    # 🚩 Insert new player row, keyed by STEAM
    conn.execute(
        """
        INSERT INTO players (server_id, eos, steam, name, coins, gold, multiplier, donor,
                             starter_used, last_daily, last_gimme, streak)
        VALUES (?, ?, ?, ?, 0, 0, 1.0, NULL, 0, 0, 0, 0)
        """,
        (server_id, eos, steam or eos, name or steam or eos),
    )
    conn.commit()

    cur = conn.execute(
        "SELECT * FROM players WHERE steam=? AND server_id=?", (steam or eos, server_id)
    )
    return dict(cur.fetchone())




def update_balance(conn, eos, server_id, coins=None, gold=None):
    if coins is not None:
        conn.execute(
            "UPDATE players SET coins=? WHERE eos=? AND server_id=?",
            (coins, eos, server_id),
        )
    if gold is not None:
        conn.execute(
            "UPDATE players SET gold=? WHERE eos=? AND server_id=?",
            (gold, eos, server_id),
        )
    conn.commit()


def update_field(conn, eos, server_id, field, value):
    conn.execute(
        f"UPDATE players SET {field}=? WHERE eos=? AND server_id=?",
        (value, eos, server_id),
    )
    conn.commit()


def update_multiplier(conn, eos, server_id, multiplier):
    conn.execute(
        "UPDATE players SET multiplier=? WHERE eos=? AND server_id=?",
        (multiplier, eos, server_id),
    )
    conn.commit()


def set_donor(conn, eos, server_id, tier):
    conn.execute(
        "UPDATE players SET donor=? WHERE eos=? AND server_id=?",
        (tier, eos, server_id),
    )
    conn.commit()


# ---------------- Teleports ----------------
def add_teleport(conn, player_id, name, pos):
    conn.execute(
        "INSERT INTO teleports (player_id, name, x, y, z) VALUES (?, ?, ?, ?, ?)",
        (player_id, name.lower(), pos[0], pos[1], pos[2]),
    )
    conn.commit()


def get_teleports(conn, player_id):
    cur = conn.execute("SELECT * FROM teleports WHERE player_id=?", (player_id,))
    return [dict(row) for row in cur.fetchall()]


def del_teleport(conn, player_id, name):
    conn.execute(
        "DELETE FROM teleports WHERE player_id=? AND name=?", (player_id, name.lower())
    )
    conn.commit()


# ---------------- Shops ----------------
def get_shop(conn, shop_type):
    cur = conn.execute("SELECT * FROM shops WHERE type=?", (shop_type,))
    return [dict(row) for row in cur.fetchall()]


# ---------------- Admins ----------------
def is_admin(conn, eos):
    # Always allow the WebAdmin user (used by the web API bridge)
    if eos == "WebAdmin":
        return True
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


# ---------------- Master Password ----------------
def get_master_password(conn):
    cur = conn.execute("SELECT value FROM settings WHERE key='master_password'")
    row = cur.fetchone()
    return row["value"] if row else None


def set_master_password(conn, pw):
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES ('master_password', ?)",
        (pw,),
    )
    conn.commit()


