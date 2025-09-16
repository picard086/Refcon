import time
import telnetlib
import sqlite3
import re
import threading

from scheduler import Scheduler
from commands import CommandHandler
from utils import load_admins

# --- NEW IMPORTS for API bridge ---
from fastapi import FastAPI, Request
import uvicorn


class EconomyBot:
    def __init__(self, server_id, name, host, port, password, conn):
        self.server_id = server_id
        self.name = name
        self.host = host
        self.port = port
        self.password = password
        self.tn = None
        self.admins = []
        self.cmd_handler = CommandHandler(self)
        self.online = {}   # {eid: {"name": str, "eos": str, "steam": str, "pos": (x,y,z)}}
        self.conn = conn   # shared database connection

    def connect(self):
        """Connect to the 7DTD server via Telnet."""
        try:
            print(f"[econ][{self.server_id} - {self.name}] Connecting to {self.host}:{self.port}...")
            self.tn = telnetlib.Telnet(self.host, int(self.port))
            self.tn.read_until(b"Please enter password:")
            self.tn.write(self.password.encode("utf-8") + b"\n")
            print(f"[econ][{self.server_id} - {self.name}] Connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"[econ][{self.server_id} - {self.name}] Telnet connection failed: {e}")
            return False

    def send(self, msg: str):
        """Send a raw command to the server and flush with rdd."""
        try:
            self.tn.write((msg + "\n").encode("utf-8"))
            time.sleep(0.05)
            self.tn.write(b"rdd\n")
        except Exception as e:
            print(f"[econ][{self.server_id} - {self.name}] Failed to send: {e}")

    def pm(self, eid: int, msg: str):
        """Send a private message to a player."""
        self.send(f"pm {eid} \"{msg}\"")

    def parse_log_line(self, line: str):
        """Parse server log lines to update online players and positions."""
        # Chat line with EOS and entity id
        chat_match = re.search(
            r"Chat \(from '(Steam_\d+|EOS_[^']+)', entity id '(\d+)'[^)]*\): '([^']+)': (/.+)",
            line
        )
        if chat_match:
            eos_or_steam, eid, name, message = chat_match.groups()
            eid = int(eid)
            if eid not in self.online:
                self.online[eid] = {}
            self.online[eid].update({"name": name, "eos": eos_or_steam, "steam": eos_or_steam})

            if message.strip().startswith("/"):
                self.cmd_handler.dispatch(message.strip(), eid, name)

        # Position update from spawn logs
        pos_match = re.search(r"PlayerSpawnedInWorld.*at \(([-\d\.]+), ([-\d\.]+), ([-\d\.]+)\)", line)
        if pos_match:
            x, y, z = map(float, pos_match.groups())
            eos_match = re.search(r"EOS_[0-9a-fA-F]+", line)
            if eos_match:
                eos = eos_match.group(0)
                for eid, pdata in self.online.items():
                    if pdata.get("eos") == eos:
                        pdata["pos"] = (x, y, z)

        # Position update from `lp` (listplayers) output
        lp_match = re.search(
            r"id=(\d+), ([^,]+), pos=\(([-\d\.]+), ([-\d\.]+), ([-\d\.]+)\)",
            line
        )
        if lp_match:
            eid = int(lp_match[1])
            name = lp_match[2].strip()
            x, y, z = float(lp_match[3]), float(lp_match[4]), float(lp_match[5])
            if eid not in self.online:
                self.online[eid] = {}
            self.online[eid].update({
                "name": name,
                "pos": (x, y, z)
            })

    def poll(self, scheduler):
        """Poll Telnet messages and feed them to command handler."""
        try:
            raw = self.tn.read_very_eager().decode("utf-8", errors="ignore")
            if raw:
                for line in raw.splitlines():
                    print(f"[econ][{self.server_id} - {self.name}] {line}")
                    self.parse_log_line(line)
                scheduler.run_pending()
        except EOFError:
            print(f"[econ][{self.server_id} - {self.name}] Telnet connection closed.")
            return False
        except Exception as e:
            print(f"[econ][{self.server_id} - {self.name}] Error in poll loop: {e}")
        return True


def run_bot(bot: EconomyBot):
    """Run one bot in its own thread."""
    bot.admins = load_admins()

    scheduler = Scheduler(bot)
    scheduler.start()

    try:
        while True:
            if not bot.poll(scheduler):
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"[econ][{bot.server_id} - {bot.name}] Shutting down bot...")
        scheduler.stop()


# ---- NEW: API Bridge ----
bot_api = FastAPI()
bot_instances = []  # keep track of all bots

@bot_api.post("/run_command")
async def run_command(request: Request):
    data = await request.json()
    cmd = data.get("cmd")
    target_server = data.get("server_id")  # optional, to target one server

    if not cmd:
        return {"status": "error", "msg": "No command provided"}

    # Select bots (all, or one if server_id given)
    bots = bot_instances
    if target_server:
        bots = [b for b in bot_instances if str(b.server_id) == str(target_server)]

    for bot in bots:
        try:
            # Pass eos explicitly
            bot.cmd_handler.dispatch(cmd, 0, "WebAdmin", "WebAdmin")
        except Exception as e:
            return {"status": "error", "msg": str(e)}

    return {"status": "ok", "cmd": cmd, "servers": [b.server_id for b in bots]}

def start_bot_api():
    uvicorn.run(bot_api, host="127.0.0.1", port=8899, log_level="info")


def main():
    print("[econ] Multi-server Economy bot starting...")

    # load all servers from DB
    conn = sqlite3.connect("economy.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, name, ip, port, password FROM servers;")
    rows = cur.fetchall()
    if not rows:
        raise RuntimeError("No servers configured in database. Run install.sh again.")

    # launch one thread per server
    threads = []
    for row in rows:
        print(f"[econ] Attempting connection to server {row['id']} ({row['name']}) at {row['ip']}:{row['port']}")
        bot = EconomyBot(row["id"], row["name"], row["ip"], row["port"], row["password"], conn)
        if bot.connect():
            print(f"[econ] Launching thread for server {row['id']} ({row['name']})")
            bot_instances.append(bot)  # keep bot for API bridge
            t = threading.Thread(target=run_bot, args=(bot,), daemon=True)
            threads.append(t)
            t.start()
        else:
            print(f"[econ] Skipping server {row['id']} ({row['name']}) - connection failed.")

    # launch bot API in background
    threading.Thread(target=start_bot_api, daemon=True).start()

    # keep main thread alive
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        print("[econ] All bots shutting down...")


if __name__ == "__main__":
    main()
