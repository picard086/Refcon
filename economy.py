import time
import telnetlib
import sqlite3
from scheduler import Scheduler
from commands import handle_command
from utils import load_admins, log


# --- Economy data ---
DONOR_TIERS = {
    "t1": {"slots": 3, "mult": 1.25, "bonus_coins": 1000, "bonus_gold": 1},
    "t2": {"slots": 6, "mult": 1.5,  "bonus_coins": 2000, "bonus_gold": 2},
    "t3": {"slots": 9, "mult": 1.75, "bonus_coins": 3000, "bonus_gold": 3},
    "t4": {"slots": 12,"mult": 2.0,  "bonus_coins": 4000,"bonus_gold": 4},
}

DONOR_PACK = [
    {"name": "qt_sarah", "amount": 1},
    {"name": "qt_taylor", "amount": 1},
    {"name": "resourceWoodBundle", "amount": 1},
    {"name": "questRewardT1SkillMagazineBundle", "amount": 2},
    {"name": "ammo9mmBulletBall", "amount": 300},
]

STARTER_PACK = [
    {"name": "drinkJarYuccaJuice", "amount": 10},
    {"name": "foodBaconAndEggs", "amount": 10},
    {"name": "meleeWpnBladeT0BoneKnife", "amount": 1},
    {"name": "vehicleBicyclePlaceable", "amount": 1},
    {"name": "armorPrimitiveOutfit", "amount": 1},
    {"name": "gunHandgunT1Pistol", "amount": 1},
    {"name": "ammo9mmBulletBall", "amount": 300},
]

GIMME_REWARDS = [
    {"name": "qt_stephan", "friendly": "Stephan's Treasure Map", "amount": 1},
    {"name": "qt_jennifer", "friendly": "Jennifer's Treasure Map", "amount": 1},
    {"name": "resourceRepairKitImp", "friendly": "Improved Repair Kit", "amount": 1},
]


# --- Bot wrapper object ---
class EconomyBot:
    def __init__(self, server_id, host, port, password):
        self.server_id = server_id
        self.host = host
        self.port = port
        self.password = password
        self.tn = None
        self.admins = []

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

    def poll(self, scheduler):
        """Poll Telnet messages and feed them to command handler."""
        try:
            msg = self.tn.read_very_eager().decode("utf-8", errors="ignore")
            if msg:
                handle_command(msg, self.tn, self.admins)
            scheduler.run_pending()
        except EOFError:
            print("[econ] Telnet connection closed.")
            return False
        except Exception as e:
            print(f"[econ] Error in poll loop: {e}")
        return True


# --- Entrypoint ---
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


