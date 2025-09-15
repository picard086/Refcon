import time
import telnetlib
import sqlite3
import re

from scheduler import Scheduler
from commands import CommandHandler
from utils import load_admins, log
from constants import DONOR_TIERS, DONOR_PACK, STARTER_PACK, GIMME_REWARDS


CHAT_REGEX = re.compile(r"INF Chat \(from .+?, entity id '(\d+)', to 'Global'\): '([^']+)':\s*(.+)")


class EconomyBot:
    def __init__(self, server_id, host, port, password):
        self.server_id = server_id
        self.host = host
        self.port = port
        self.password = password
        self.tn = None
        self.admins = []
        self.cmd_handler = CommandHandler(self)
        self.online = {}
        self.conn = None  # DB connection

    def connect(self):
        """Connect to the 7DTD server via Telnet."""
        try:
            self.tn = telnetlib.Telnet(self.host, int(self.port))
            self.tn.read_until(b"Please enter password:")
            self.tn.write(self.password.encode("utf-8") + b"\n")
            print(f"[econ] Connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"[econ] Telnet connection failed: {e}")
            return False

    def send(self, msg: str):
        """Send a raw command to the server."""
        try:
            self.tn.write(msg.encode("utf-8") + b"\n")
        except Exception as e:
            print(f"[econ] Failed to send: {e}")

    def pm(self, eid: int, msg: str):
        """Send a private message to a player."""
        self.send(f"pm {eid} \"{msg}\"")

    def _dispatch(self, line: str):
        """
        Handle raw telnet log lines, look for chat commands,
        and feed them to CommandHandler.
        """
        m = CHAT_REGEX.search(line)
        if m:
            eid = int(m.group(1))
            name = m.group(2)
            msg = m.group(3).strip()
            print(f"[econ] Chat command from {name} (id={eid}): {msg}", flush=True)
            self.cmd_handler.dispatch(msg, eid, name)

    def poll(self, scheduler):
        """Poll Telnet messages and feed them to command handler."""
        try:
            raw = self.tn.read_very_eager().decode("utf-8", errors="ignore")
            if raw:
                for line in raw.splitlines():
                    if line.strip():
                        print(f"[econ] {line}", flush=True)
                        self._dispatch(line)

            scheduler.run_pending()

        except EOFError:
            print("[econ] Telnet connection closed. Attempting reconnect...")
            if not self.connect():
                return False
        except Exception as e:
            print(f"[econ] Error in poll loop: {e}")
        return True


def main():
    print("[econ] Economy bot main loop starting...")

    # load server config from DB
    conn = sqlite3.connect("economy.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, ip, port, password FROM servers LIMIT 1;")
    row = cur.fetchone()
    if not row:
        raise RuntimeError("No server configured in database. Run install.sh again.")

    bot = EconomyBot(row["id"], row["ip"], row["port"], row["password"])
    bot.conn = conn  # attach db connection so commands can use it

    if not bot.connect():
        return

    # load admins from JSON/DB
    bot.admins = load_admins()

    # scheduler bound to this bot
    scheduler = Scheduler(bot)

    # main loop
    try:
        while True:
            if not bot.poll(scheduler):
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("[econ] Shutting down bot...")


if __name__ == "__main__":
    main()
