import shlex, time, threading, requests
from db import (
    get_player, update_balance, update_field,
    get_shop, add_teleport, get_teleports, del_teleport,
    is_admin, add_admin, get_vote, save_vote
)
from utils import COL_OK, COL_WARN, COL_ERR, COL_INFO, COL_GOLD, COL_END
from economy import DONOR_TIERS, DONOR_PACK, STARTER_PACK, GIMME_REWARDS

class CommandHandler:
    def __init__(self, bot):
        self.bot = bot

    def dispatch(self, line: str):
        if "INF Chat" not in line or "entity id" not in line:
            return
        eid = int(line.split("entity id '")[1].split("'")[0])
        msg = line.split("):", 1)[1].strip()
        eos = self.bot.online.get(eid, {}).get("eos", str(eid))
        pdata = get_player(self.bot.conn, eos, self.bot.server_id)

        # ---------------- Basics ----------------
        if msg == "/ping":
            self.bot.pm(eid, f"{COL_OK}pong{COL_END}")
        elif msg == "/balance":
            self.bot.pm(eid, f"{COL_GOLD}Balance: {pdata['coins']} Refuge Coins (x{pdata['multiplier']}){COL_END}")
        elif msg == "/goldbalance":
            self.bot.pm(eid, f"{COL_GOLD}Gold Balance: {pdata['gold']} Refuge Gold{COL_END}")

        # ---------------- Shops ----------------
        elif msg.startswith("/shop"):
            items = get_shop(self.bot.conn, "coin")
            for i in items:
                self.bot.pm(eid, f"{COL_GOLD}ID {i['id']}: {i['friendly']} - {i['price']} coins{COL_END}")
            self.bot.pm(eid, f"{COL_INFO}Use /buy <id>{COL_END}")

        elif msg.startswith("/buy"):
            p = shlex.split(msg)
            if len(p) < 2: return self.bot.pm(eid, f"{COL_INFO}Usage: /buy <id>{COL_END}")
            iid = int(p[1])
            items = get_shop(self.bot.conn, "coin")
            it = next((x for x in items if x["id"] == iid), None)
            if not it: return self.bot.pm(eid, f"{COL_ERR}Item not found.{COL_END}")
            if pdata["coins"] < it["price"]:
                return self.bot.pm(eid, f"{COL_ERR}Not enough coins.{COL_END}")
            new_balance = pdata["coins"] - it["price"]
            update_balance(self.bot.conn, eos, self.bot.server_id, coins=new_balance)
            self.bot.send(f"giveplus {eid} {it['item_name']} {it['amount']}")
            self.bot.pm(eid, f"{COL_OK}Purchased {it['friendly']}!{COL_END}")

        elif msg.startswith("/goldshop"):
            items = get_shop(self.bot.conn, "gold")
            for i in items:
                self.bot.pm(eid, f"{COL_GOLD}ID {i['id']}: {i['friendly']} - {i['price']} gold{COL_END}")
            self.bot.pm(eid, f"{COL_INFO}Use /goldbuy <id>{COL_END}")

        elif msg.startswith("/goldbuy"):
            p = shlex.split(msg)
            if len(p) < 2: return self.bot.pm(eid, f"{COL_INFO}Usage: /goldbuy <id>{COL_END}")
            iid = int(p[1])
            items = get_shop(self.bot.conn, "gold")
            it = next((x for x in items if x["id"] == iid), None)
            if not it: return self.bot.pm(eid, f"{COL_ERR}Item not found.{COL_END}")
            if pdata["gold"] < it["price"]:
                return self.bot.pm(eid, f"{COL_ERR}Not enough gold.{COL_END}")
            new_gold = pdata["gold"] - it["price"]
            update_balance(self.bot.conn, eos, self.bot.server_id, gold=new_gold)
            self.bot.send(f"giveplus {eid} {it['item_name']} {it['amount']}")
            self.bot.pm(eid, f"{COL_OK}Purchased {it['friendly']} with gold!{COL_END}")

        # ---------------- Donors ----------------
        elif msg.startswith("/adddonor"):
            if not is_admin(self.bot.conn, eos):
                return self.bot.pm(eid, f"{COL_ERR}Not admin.{COL_END}")
            p = shlex.split(msg)
            if len(p) < 3: return self.bot.pm(eid, f"{COL_INFO}Usage: /adddonor <name> <t1-t4>{COL_END}")
            tier = p[2].lower()
            if tier not in DONOR_TIERS:
                return self.bot.pm(eid, f"{COL_ERR}Invalid tier.{COL_END}")
            update_field(self.bot.conn, eos, self.bot.server_id, "donor", tier)
            update_field(self.bot.conn, eos, self.bot.server_id, "multiplier", DONOR_TIERS[tier]["mult"])
            self.bot.pm(eid, f"{COL_OK}Set donor tier {tier.upper()}.{COL_END}")

        elif msg.startswith("/removedonor"):
            if not is_admin(self.bot.conn, eos):
                return self.bot.pm(eid, f"{COL_ERR}Not admin.{COL_END}")
            update_field(self.bot.conn, eos, self.bot.server_id, "donor", None)
            update_field(self.bot.conn, eos, self.bot.server_id, "multiplier", 1.0)
            self.bot.pm(eid, f"{COL_OK}Removed donor status.{COL_END}")

        elif msg == "/donor":
            if not pdata["donor"]: return self.bot.pm(eid, f"{COL_ERR}Not a donor.{COL_END}")
            if pdata["donor_used"]: return self.bot.pm(eid, f"{COL_WARN}Already claimed donor pack.{COL_END}")
            for i in DONOR_PACK:
                self.bot.send(f"giveplus {eid} {i['name']} {i['amount']}")
            update_field(self.bot.conn, eos, self.bot.server_id, "donor_used", 1)
            self.bot.pm(eid, f"{COL_OK}Donor pack claimed!{COL_END}")

        # ---------------- Kits ----------------
        elif msg == "/starterkit":
            if pdata["starter_used"]: return self.bot.pm(eid, f"{COL_WARN}Already claimed starter kit.{COL_END}")
            for i in STARTER_PACK:
                self.bot.send(f"giveplus {eid} {i['name']} {i['amount']}")
            update_field(self.bot.conn, eos, self.bot.server_id, "starter_used", 1)
            self.bot.pm(eid, f"{COL_OK}Starter kit claimed!{COL_END}")

        elif msg == "/gimme":
            now = time.time()
            last = pdata["last_gimme"] or 0
            if now - last < 6 * 3600:
                return self.bot.pm(eid, f"{COL_WARN}Cooldown active.{COL_END}")
            import random
            reward = random.choice(GIMME_REWARDS)
            self.bot.send(f"giveplus {eid} {reward['name']} {reward['amount']}")
            update_field(self.bot.conn, eos, self.bot.server_id, "last_gimme", int(now))
            self.bot.pm(eid, f"{COL_OK}You got {reward['friendly']}!{COL_END}")

        elif msg == "/daily":
            now = int(time.time())
            last = pdata["last_daily"] or 0
            if now - last < 24 * 3600:
                return self.bot.pm(eid, f"{COL_WARN}Already claimed daily.{COL_END}")
            coins = 500
            update_balance(self.bot.conn, eos, self.bot.server_id, coins=pdata["coins"] + coins)
            update_field(self.bot.conn, eos, self.bot.server_id, "last_daily", now)
            self.bot.pm(eid, f"{COL_OK}+{coins} daily Refuge Coins!{COL_END}")

        # ---------------- Teleports ----------------
        elif msg.startswith("/settp"):
            p = shlex.split(msg)
            if len(p) < 2: return self.bot.pm(eid, f"{COL_INFO}Usage: /settp <name>{COL_END}")
            pos = self.bot.online.get(eid, {}).get("pos", (0, 0, 0))
            add_teleport(self.bot.conn, pdata["id"], p[1], pos)
            self.bot.pm(eid, f"{COL_OK}Teleport '{p[1]}' saved.{COL_END}")

        elif msg == "/tplist":
            tps = get_teleports(self.bot.conn, pdata["id"])
            if not tps: return self.bot.pm(eid, f"{COL_INFO}No teleports saved.{COL_END}")
            for tp in tps:
                self.bot.pm(eid, f"{COL_GOLD}{tp['name']}{COL_END} -> ({tp['x']}, {tp['y']}, {tp['z']})")

        elif msg.startswith("/deltp"):
            p = shlex.split(msg)
            if len(p) < 2: return self.bot.pm(eid, f"{COL_INFO}Usage: /deltp <name>{COL_END}")
            del_teleport(self.bot.conn, pdata["id"], p[1])
            self.bot.pm(eid, f"{COL_OK}Teleport '{p[1]}' deleted.{COL_END}")

        # ---------------- Admin ----------------
        elif msg.startswith("/addcoins"):
            if not is_admin(self.bot.conn, eos):
                return self.bot.pm(eid, f"{COL_ERR}Not admin.{COL_END}")
            p = shlex.split(msg)
            if len(p) < 3: return
            target_name, amt = p[1], int(p[2])
            target = next((v for v in self.bot.online.values() if v["name"].lower() == target_name.lower()), None)
            if not target: return self.bot.pm(eid, f"{COL_ERR}Target not online.{COL_END}")
            tdata = get_player(self.bot.conn, target["eos"], self.bot.server_id)
            update_balance(self.bot.conn, target["eos"], self.bot.server_id, coins=tdata["coins"] + amt)
            self.bot.pm(eid, f"{COL_OK}Added {amt} coins to {target_name}.{COL_END}")

        elif msg.startswith("/addadmins"):
            if not is_admin(self.bot.conn, eos):
                return self.bot.pm(eid, f"{COL_ERR}Not admin.{COL_END}")
            p = shlex.split(msg)
            if len(p) < 2: return
            target_name = p[1]
            target = next((v for v in self.bot.online.values() if v["name"].lower() == target_name.lower()), None)
            if not target: return self.bot.pm(eid, f"{COL_ERR}Target not online.{COL_END}")
            add_admin(self.bot.conn, target["eos"])
            self.bot.pm(eid, f"{COL_OK}{target_name} is now admin.{COL_END}")

        # ---------------- Vote ----------------
        elif msg == "/vote":
            api_key = "REPLACE_WITH_REAL_API_KEY"
            steamid = self.bot.online.get(eid, {}).get("steam", None)
            if not steamid or steamid == "0":
                return self.bot.pm(eid, f"{COL_WARN}No SteamID found.{COL_END}")
            url = f"https://7daystodie-servers.com/api/?action=post&object=votes&element=claim&key={api_key}&steamid={steamid}"
            try:
                resp = requests.get(url, timeout=10)
                if "1" in resp.text:
                    now = int(time.time())
                    save_vote(self.bot.conn, eos, now)
                    self.bot.pm(eid, f"{COL_OK}Thanks for voting! You’ve been rewarded.{COL_END}")
                else:
                    self.bot.pm(eid, f"{COL_WARN}No vote found yet.{COL_END}")
            except Exception:
                self.bot.pm(eid, f"{COL_ERR}Vote check failed.{COL_END}")
