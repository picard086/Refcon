import time
import telnetlib
import sqlite3
import re
import threading

from scheduler import Scheduler
from commands import CommandHandler
from utils import load_admins

# --- NEW IMPORTS for API bridge + web UI ---
from fastapi import FastAPI, Request, Form
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

        # --- attach scheduler to each bot ---
        self.scheduler = Scheduler(self)

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
        print(f"[econ][DEBUG] RAW: {line}")
        """Parse server log lines to update online players and positions."""

        # --- Chat lines (unchanged) ---
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

        # --- LP output (rebuild online list) ---
        lp_match = re.search(
            r"id=(\d+), ([^,]+), pos=\(([^)]+)\).*pltfmid=([^,]+), crossid=([^,]+)",
            line
        )
        if lp_match:
            eid = int(lp_match[1])
            name = lp_match[2].strip()
            x, y, z = float(lp_match[3]), float(lp_match[4]), float(lp_match[5])
            pltfmid = lp_match[6].strip()
            crossid = lp_match[7].strip()

            if not hasattr(self, "_lp_batch"):
                self._lp_batch = {}

            self._lp_batch[eid] = {
                "name": name,
                "pos": (x, y, z),
                "steam": pltfmid if pltfmid.startswith("Steam_") else None,
                "eos": crossid if crossid.startswith("EOS_") else None
            }

        # --- End of LP dump detection ---
        if "Total of" in line and "in the game" in line:
            if hasattr(self, "_lp_batch"):
                self.online = self._lp_batch
                del self._lp_batch


def poll(self):
    """Poll Telnet messages and dump raw output for debug."""
    try:
        raw = self.tn.read_very_eager().decode("utf-8", errors="ignore")
        if raw:
            print(f"[econ][{self.server_id} - {self.name}][RAW]\n{raw}")
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

    # Make lp run every 10s instead of 30
    scheduler = Scheduler(bot, income_interval=60, lp_interval=10)
    bot.scheduler = scheduler  # attach so bot has a reference
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

# --- Economy/Admin routes ---
@bot_api.post("/web_adddonor")
async def web_adddonor(request: Request, player: str = Form(...), tier: str = Form(...), server_id: int = Form(...)):
    return await _dispatch_command(request, f"/adddonor {player} {tier}", server_id, f"{player} is now donor {tier.upper()}")

@bot_api.post("/web_addgold")
async def web_addgold(request: Request, player: str = Form(...), amount: int = Form(...), server_id: int = Form(...)):
    return await _dispatch_command(request, f"/addgold {player} {amount}", server_id, f"Added {amount} gold to {player}")

@bot_api.post("/web_checkplayer")
async def web_checkplayer(request: Request, player: str = Form(...), server_id: int = Form(...)):
    return await _dispatch_command(request, f"/checkplayer {player}", server_id, f"Checked {player}'s info")

@bot_api.post("/web_pm")
async def web_pm(request: Request, player: str = Form(...), message: str = Form(...), server_id: int = Form(...)):
    return await _dispatch_command(request, f"/pm {player} {message}", server_id, f"Sent PM to {player}")

# --- Rewards ---
@bot_api.post("/web_gimme")
async def web_gimme(request: Request, server_id: int = Form(...)):
    return await _dispatch_command(request, "/gimme", server_id, "Triggered gimme")

@bot_api.post("/web_daily")
async def web_daily(request: Request, server_id: int = Form(...)):
    return await _dispatch_command(request, "/daily", server_id, "Triggered daily")

@bot_api.post("/web_vote")
async def web_vote(request: Request, server_id: int = Form(...)):
    return await _dispatch_command(request, "/vote", server_id, "Vote saved")

@bot_api.post("/web_starterkit")
async def web_starterkit(request: Request, player: str = Form(...), server_id: int = Form(...)):
    return await _dispatch_command(request, f"/starterkit {player}", server_id, f"Gave starter kit to {player}")

@bot_api.post("/web_donorpack")
async def web_donorpack(request: Request, player: str = Form(...), server_id: int = Form(...)):
    return await _dispatch_command(request, f"/donor {player}", server_id, f"Gave donor pack to {player}")

# --- Teleports ---
@bot_api.post("/web_settp")
async def web_settp(request: Request, player: str = Form(...), tpname: str = Form(...), server_id: int = Form(...)):
    return await _dispatch_command(request, f"/settp {tpname}", server_id, f"{player} set TP {tpname}")

@bot_api.post("/web_tplist")
async def web_tplist(request: Request, player: str = Form(...), server_id: int = Form(...)):
    return await _dispatch_command(request, "/tplist", server_id, f"Listed TPs for {player}")

@bot_api.post("/web_deltp")
async def web_deltp(request: Request, tpname: str = Form(...), server_id: int = Form(...)):
    return await _dispatch_command(request, f"/deltp {tpname}", server_id, f"Deleted TP {tpname}")

@bot_api.post("/web_tp")
async def web_tp(request: Request, player: str = Form(...), tpname: str = Form(...), server_id: int = Form(...)):
    return await _dispatch_command(request, f"/tp {tpname}", server_id, f"Teleported {player} to {tpname}")

# --- Shops ---
@bot_api.post("/web_shop")
async def web_shop(request: Request, server_id: int = Form(...)):
    return await _dispatch_command(request, "/shop", server_id, "Opened shop")

@bot_api.post("/web_goldshop")
async def web_goldshop(request: Request, server_id: int = Form(...)):
    return await _dispatch_command(request, "/goldshop", server_id, "Opened gold shop")

@bot_api.post("/web_buy")
async def web_buy(request: Request, itemid: int = Form(...), server_id: int = Form(...)):
    return await _dispatch_command(request, f"/buy {itemid}", server_id, f"Bought item {itemid}")

@bot_api.post("/web_goldbuy")
async def web_goldbuy(request: Request, itemid: int = Form(...), server_id: int = Form(...)):
    return await _dispatch_command(request, f"/goldbuy {itemid}", server_id, f"Bought item {itemid} with gold")

# --- Utility ---
@bot_api.post("/web_soil")
async def web_soil(request: Request, server_id: int = Form(...)):
    return await _dispatch_command(request, "/soil", server_id, "Triggered soil command")

@bot_api.post("/web_say")
async def web_say(request: Request, message: str = Form(...), server_id: int = Form(...)):
    return await _dispatch_command(request, f"/say {message}", server_id, f"Said: {message}")

@bot_api.post("/web_kick")
async def web_kick(request: Request, player: str = Form(...), server_id: int = Form(...)):
    bots = [b for b in bot_instances if str(b.server_id) == str(server_id)]
    if not bots:
        return templates.TemplateResponse("index.html", {"request": request, "msg": "Server not found"})
    try:
        bot = bots[0]
        # Send a raw console command so it works
        bot.send(f'kick "{player}"')
        return templates.TemplateResponse("index.html", {"request": request, "msg": f"Kicked {player}"})
    except Exception as e:
        return templates.TemplateResponse("index.html", {"request": request, "msg": str(e)})


@bot_api.post("/web_ban")
async def web_ban(request: Request, player: str = Form(...), server_id: int = Form(...)):
    return await _dispatch_command(request, f"/ban {player}", server_id, f"Banned {player}")

# --- Online players as JSON (skip WebAdmin) ---
@bot_api.get("/online_players")
async def online_players():
    data = {}
    for bot in bot_instances:
        players = []
        for eid, pdata in bot.online.items():
            if pdata.get("name") == "WebAdmin":
                continue
            players.append({
                "eid": eid,
                "name": pdata.get("name"),
                "eos": pdata.get("eos"),
                "steam": pdata.get("steam"),
                "pos": pdata.get("pos")
            })
        data[bot.server_id] = players
    return data


# --- Shared dispatcher helpers ---
async def _dispatch_command(request: Request, cmd: str, server_id: int, success_msg: str):
    bots = [b for b in bot_instances if str(b.server_id) == str(server_id)]
    for bot in bots:
        try:
            # Always run as WebAdmin (authority), but don’t overwrite the player in cmd
            bot.online[0] = {"name": "WebAdmin", "eos": "WebAdmin", "steam": "WebAdmin"}
            bot.cmd_handler.dispatch(cmd, 0, "WebAdmin", "WebAdmin")
            return templates.TemplateResponse("index.html", {"request": request, "msg": success_msg})
        except Exception as e:
            return templates.TemplateResponse("index.html", {"request": request, "msg": str(e)})
    return templates.TemplateResponse("index.html", {"request": request, "msg": "Server not found"})


def _dispatch_json(cmd: str, target_server: int = None):
    bots = bot_instances
    if target_server:
        bots = [b for b in bot_instances if str(b.server_id) == str(target_server)]

    for bot in bots:
        try:
            bot.online[0] = {"name": "WebAdmin", "eos": "WebAdmin", "steam": "WebAdmin"}
            bot.cmd_handler.dispatch(cmd, 0, "WebAdmin", "WebAdmin")
        except Exception as e:
            return {"status": "error", "msg": str(e)}

    return {"status": "ok", "cmd": cmd, "servers": [b.server_id for b in bots]}


def start_bot_api():
    uvicorn.run(bot_api, host="0.0.0.0", port=8848, log_level="info")


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
            bot_instances.append(bot)

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









