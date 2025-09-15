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


# --- Entrypoint ---
def main():
    print("[econ] Economy bot main loop starting...")

    # load server config from DB
    conn = sqlite3.connect("economy.db")
    cur = conn.cursor()
    cur.execute("SELECT ip, port, password FROM servers LIMIT 1;")
    row = cur.fetchone()
    if not row:
        raise RuntimeError("No server configured in database. Run install.sh again.")
    host, port, password = row
    conn.close()

    # connect telnet
    try:
        tn = telnetlib.Telnet(host, int(port))
        tn.read_until(b"Please enter password:")
        tn.write(password.encode("utf-8") + b"\n")
        print(f"[econ] Connected to {host}:{port}")
    except Exception as e:
        print(f"[econ] Telnet connection failed: {e}")
        return

    # load admins
    admins = load_admins()

    # scheduler
    scheduler = Scheduler()

    # main loop
    try:
        while True:
            msg = tn.read_very_eager().decode("utf-8", errors="ignore")
            if msg:
                handle_command(msg, tn, admins)

            scheduler.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("[econ] Shutting down bot...")


if __name__ == "__main__":
    main()


