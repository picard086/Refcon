# ---------------- Colors ----------------
COL_OK   = "[00ff00]"
COL_WARN = "[ffff00]"
COL_ERR  = "[ff0000]"
COL_INFO = "[00ffff]"
COL_GOLD = "[ffcc00]"
COL_END  = "[-]"

# ---------------- Logging ----------------
def log(msg: str, level: str = "INFO"):
    """Simple logger wrapper for economy bot."""
    print(f"[econ][{level}] {msg}", flush=True)

# ---------------- Formatting ----------------
def format_msg(parts):
    """
    Build a color-coded message from a list of (color, text).
    Example:
        format_msg([(COL_OK, "Success!"), (COL_INFO, "Coins added")])
    """
    return "".join([f"{c}{t}{COL_END}" for c, t in parts])

# ---------------- Admin Loader ----------------
import sqlite3

def load_admins():
    """
    Load admin EOS IDs from the SQLite database.
    Expects a table `admins` with at least a column `eos`.
    """
    try:
        conn = sqlite3.connect("economy.db")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS admins (eos TEXT PRIMARY KEY)")
        rows = cur.execute("SELECT eos FROM admins").fetchall()
        return [r["eos"] for r in rows]
    except Exception as e:
        log(f"Failed to load admins: {e}", "ERR")
        return []
