import time
import telnetlib
import sqlite3
import re
import threading

from scheduler import Scheduler
from commands import CommandHandler
from utils import load_admins
from db import get_player, get_teleports, add_teleport, del_teleport

# --- NEW IMPORTS for API bridge + web UI ---
from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
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
            account_id, eid, name, message = chat_match.groups()
            eid = int(eid)

            account_id = account_id.strip().rstrip(",")
            eos_id = account_id if account_id.startswith("EOS_") else None
            steam_id = account_id if account_id.startswith("Steam_") else None

            if eid not in self.online:
                self.online[eid] = {}

            self.online[eid].update({
                "name": name,
                "eos": eos_id,
                "steam": steam_id
            })

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
            r"id=(\d+),\s*([^,]+),\s*pos=\(([-\d\.]+), ([-\d\.]+), ([-\d\.]+)\).*pltfmid=(\S+), crossid=(\S+)",
            line
        )
        if lp_match:
            eid = int(lp_match[1])
            name = lp_match[2].strip()
            x, y, z = float(lp_match[3]), float(lp_match[4]), float(lp_match[5])
            steam_id = lp_match[6].strip().rstrip(",")
            eos_id = lp_match[7].strip().rstrip(",")

            if eid not in self.online:
                self.online[eid] = {}

            self.online[eid].update({
                "name": name,
                "pos": (x, y, z),
                "steam": steam_id or self.online[eid].get("steam"),
                "eos": eos_id or self.online[eid].get("eos")
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
    if "WebAdmin" not in bot.admins:
        bot.admins.append("WebAdmin")

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

# ---- NEW: Web UI (templates + routes) ----
templates = Jinja2Templates(directory="templates")

@bot_api.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# --- Online players as JSON (skip WebAdmin) ---
@bot_api.get("/online_players")
async def online_players():
    data = {}
    for bot in bot_instances:
        players = []
        for eid, pdata in bot.online.items():
            if pdata.get("name") == "WebAdmin":
                continue

            eos = (pdata.get("eos") or "").rstrip(",")
            steam = (pdata.get("steam") or "").rstrip(",")
            name = pdata.get("name")

            row = get_player(bot.conn, eos or steam or name, bot.server_id, name, steam)
            player_id = row["id"] if row else None

            players.append({
                "eid": eid,
                "name": name,
                "id": eos or steam or "?",
                "steam": steam,
                "pos": pdata.get("pos"),
                "player_id": player_id
            })
        data[bot.server_id] = players
    return data


# --- Teleports API ---
@bot_api.get("/web_get_tps")
async def web_get_tps(player_id: int = Query(...)):
    return get_teleports(bot_instances[0].conn, player_id)

@bot_api.post("/web_addtp")
async def web_addtp(player_id: int = Form(...), name: str = Form(...), x: float = Form(...), y: float = Form(...), z: float = Form(...)):
    add_teleport(bot_instances[0].conn, player_id, name, (x, y, z))
    return {"status": "ok"}

@bot_api.post("/web_deltp")
async def web_deltp(player_id: int = Form(...), name: str = Form(...)):
    del_teleport(bot_instances[0].conn, player_id, name)
    return {"status": "ok"}


# --- Shared dispatcher helpers ---
async def _dispatch_command(request: Request, cmd: str, server_id: int, success_msg: str):
    bots = [b for b in bot_instances if str(b.server_id) == str(server_id)]
    for bot in bots:
        try:
            bot.online[0] = {"name": "WebAdmin", "eos": "WebAdmin", "steam": "WebAdmin"}
            bot.cmd_handler.dispatch(cmd, 0, "WebAdmin", "WebAdmin")
            return templates.TemplateResponse("index.html", {"request": request, "msg": success_msg})
        except Exception as e:
            return templates.TemplateResponse("index.html", {"request": request, "msg": str(e)})
    return templates.TemplateResponse("index.html", {"request": request, "msg": "Server not found"})


def start_bot_api():
    uvicorn.run(bot_api, host="0.0.0.0", port=8848, log_level="info")


def main():
    print("[econ] Multi-server Economy bot starting...")

    conn = sqlite3.connect("economy.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, name, ip, port, password FROM servers;")
    rows = cur.fetchall()
    if not rows:
        raise RuntimeError("No servers configured in database. Run install.sh again.")

    threads = []
    for row in rows:
        print(f"[econ] Attempting connection to server {row['id']} ({row['name']}) at {row['ip']}:{row['port']}")
        bot = EconomyBot(row["id"], row["name"], row["ip"], row["port"], row["password"], conn)
        if bot.connect():
            print(f"[econ] Launching thread for server {row['id']} ({row['name']})")
            bot_instances.append(bot)
            t = threading.Thread(target=run_bot, args=(bot,), daemon=True)
            threads.append(t)
            t.start()
        else:
            print(f"[econ] Skipping server {row['id']} ({row['name']}) - connection failed.")

    threading.Thread(target=start_bot_api, daemon=True).start()

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        print("[econ] All bots shutting down...")


if __name__ == "__main__":
    main()
