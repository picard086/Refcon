import time
import telnetlib
import sqlite3
import re
import threading

from scheduler import Scheduler
from commands import CommandHandler
from utils import load_admins, log
from constants import DONOR_TIERS, DONOR_PACK, STARTER_PACK, GIMME_REWARDS


class EconomyBot:
    def __init__(self, server_id, host, port, password):
        self.server_id = server_id
        self.host = host
        self.port = port
        self.password = password
        self.tn = None
        self.admins = []
        self.cmd_handler = CommandHandler(self)
        self.online = {}   # {eid: {"name": str, "eos": str, "steam": str, "pos": (x,y,z)}}
        self.conn = None   # database connection

    def connect(self):
        """Connect to the 7DTD server via Telnet."""
        try:
            self.tn = telnetlib.Telnet(self.host, int(self.port))
            self.tn.read_until(b"Please enter password:")
            self.tn.write(self.password.encode("utf-8") + b"\n")
            print(f"[econ] Connected to {self.host}:{self.port}")

            # Start heartbeat (lp every 20s)
            threading.Thread(target=self.heartbeat, daemon=True).start()
            return True
        except Exception as e:
            print(f"[econ] Telnet connection failed: {e}")
            return False

    def heartbeat(self):
        """Periodically ask server for player list (lp) to keep online data fresh."""
        while True:
            try:
                self.send("lp")
            except Exception as e:
                print(f"[econ] Heartbeat error: {e}")
            time.sleep(20)

    def send(self, msg: str):
        """Send a raw command to the server, then flush with rdd."""
        try:
            self.tn.write((msg + "\n").encode("utf-8"))
            self.tn.write(b"rdd\n")  # flush trick
        except Exception as e:
            print(f"[econ] Failed to send: {e}")

    def pm(self, eid: int, msg: str):
        """Send a private message to a player."""
        self.send(f"pm {eid} \"{msg}\"")

    def parse_log_line(self, line: str):
        """Parse server log lines to update online players and positions."""
        # Chat line with EOS and entity id
        chat_match = re.search(r"Chat \(from '(Steam_\d+|EOS_[^']+)', entity id '(\d+)'[^)]*\): '([^']+)'", line)
        if chat_match:
            eos_or_steam, eid, name = chat_match.groups()
            eid = int(eid)
            if eid not in self.online:
                self.online[eid] = {}
            self.online[eid].update({"name": name, "eos": eos_or_steam, "steam": eos_or_steam})

        # Position update (PlayerSpawnedInWorld or similar)
        pos_match = re.search(r"PlayerSpawnedInWorld.*at \(([-\d\.]+), ([-\d\.]+), ([-\d\.]+)\)", line)
        if pos_match:
            x, y, z = map(float, pos_match.groups())
            # Sometimes EOS id is on the same line
            eos_match = re.search(r"EOS_[0-9a-fA-F]+", line)
            if eos_match:
                eos = eos_match.group(0)
                for eid, pdata in self.online.items():
                    if pdata.get("eos") == eos:
                        pdata["pos"] = (x, y, z)

    def poll(self, scheduler):
        """Poll Telnet messages and feed them to command handler."""
        try:
            raw = self.tn.read_very_eager().decode("utf-8", errors="ignore")
            if raw:
                for line in raw.splitlines():
                    print(f"[econ] {line}")
                    self.parse_log_line(line)

                    # --- NEW: detect chat commands ---
                    chat_match = re.search(
                        r"Chat \(from '(Steam_\d+|EOS_[^']+)', entity id '(\d+)'[^)]*\): '([^']+)'",
                        line
                    )
                    if chat_match:
                        eos_or_steam, eid, msg = chat_match.groups()
                        eid = int(eid)
                        name = self.online.get(eid, {}).get("name", "")
                        if msg.startswith("/"):
                            self.cmd_handler.dispatch(msg.strip(), eid, name)

                scheduler.run_pending()
        except EOFError:
            print("[econ] Telnet connection closed.")
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
    bot.conn = conn  # keep DB connection available to handlers

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

