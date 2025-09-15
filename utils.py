# utils.py

# ---------------- Colors ----------------
COL_OK   = "[00ff00]"
COL_WARN = "[ffff00]"
COL_ERR  = "[ff0000]"
COL_INFO = "[00ffff]"
COL_GOLD = "[ffcc00]"
COL_END  = "[-]"

# ---------------- Logging ----------------
def log(msg: str):
    """Simple logger wrapper for economy bot."""
    print(f"[econ] {msg}", flush=True)

# ---------------- Admin Loader ----------------
def load_admins():
    """
    Stubbed admin loader.
    In the future, this could read from a JSON/DB, 
    but for now just return an empty list.
    """
    return []
