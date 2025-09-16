import shlex, time, requests, threading, random
from db import (
    get_player, update_balance, update_field,
    add_teleport, get_teleports, del_teleport,
    is_admin, add_admin, save_vote,
    get_master_password
)
from utils import COL_OK, COL_WARN, COL_ERR, COL_INFO, COL_GOLD, COL_END
from constants import (
    DONOR_TIERS, DONOR_PACK, STARTER_PACK, GIMME_REWARDS,
    DEFAULT_SHOP, DEFAULT_GOLDSHOP
)


class CommandHandler:
    def __init__(self, bot):
        self.bot = bot

    # -------- helpers --------
    def _find_online_by_name(self, name_lower):
        """Return (eid, rec) for the exact-name (case-insensitive) match, else (None, None)."""
        for teid, rec in self.bot.online.items():
            if rec.get("name", "").lower() == name_lower:
                return teid, rec
        return None, None

    def dispatch(self, msg: str, eid: int, name: str):
        """Handle a parsed chat command from a player."""
        eos = self.bot.online.get(eid, {}).get("eos", str(eid))
        pdata = get_player(self.bot.conn, eos, self.bot.server_id)

        # ---------------- Basics ----------------
        if msg == "/ping":
            self.bot.pm(eid, f"{COL_OK}pong{COL_END}")
        elif msg == "/balance":
            self.bot.pm(eid, f"{COL_GOLD}Balance: {pdata['coins']} Refuge Coins (x{pdata['multiplier']}){COL_END}")
        elif msg == "/goldbalance":
            self.bot.pm(eid, f"{COL_GOLD}Gold Balance: {pdata['gold']} Refuge Gold{COL_END}")

        elif msg == "/help":
            self.bot.pm(eid, f"{COL_INFO}--- Refuge Commands ---{COL_END}")
            self.bot.pm(eid, "/balance, /goldbalance, /shop, /buy, /goldshop, /goldbuy")
            self.bot.pm(eid, "/starterkit, /donor, /gimme, /soil, /daily")
            self.bot.pm(eid, "/settp, /tp, /tplist, /deltp")
            self.bot.pm(eid, "/beammeupscotty, /vote")
            self.bot.pm(eid, "Vehicle recall: /findbike /find4x4 /findgyro /finddrone")

        # ---------------- Shops ----------------
        elif msg.startswith("/shop"):
            for i in DEFAULT_SHOP:
                self.bot.pm(eid, f"{COL_GOLD}ID {i['id']}: {i['friendly']} - {i['price']} coins{COL_END}")
            self.bot.pm(eid, f"{COL_INFO}Use /buy <id>{COL_END}")

        elif msg.startswith("/buy"):
            p = shlex.split(msg)
            if len(p) < 2:
                return self.bot.pm(eid, f"{COL_INFO}Usage: /buy <id>{COL_END}")
            iid = int(p[1])
            it = next((x for x in DEFAULT_SHOP if x["id"] == iid), None)
            if not it:
                return self.bot.pm(eid, f"{COL_ERR}Item not found.{COL_END}")
            if pdata["coins"] < it["price"]:
                return self.bot.pm(eid, f"{COL_ERR}Not enough coins.{COL_END}")
            new_balance = pdata["coins"] - it["price"]
            update_balance(self.bot.conn, eos, self.bot.server_id, coins=new_balance)
            self.bot.send(f"giveplus {eid} {it['name']} {it['amount']}")
            self.bot.pm(eid, f"{COL_OK}Purchased {it['friendly']}!{COL_END}")

        elif msg.startswith("/goldshop"):
            for i in DEFAULT_GOLDSHOP:
                self.bot.pm(eid, f"{COL_GOLD}ID {i['id']}: {i['friendly']} - {i['price']} gold{COL_END}")
            self.bot.pm(eid, f"{COL_INFO}Use /goldbuy <id>{COL_END}")

        elif msg.startswith("/goldbuy"):
            p = shlex.split(msg)
            if len(p) < 2:
                return self.bot.pm(eid, f"{COL_INFO}Usage: /goldbuy <id>{COL_END}")
            iid = int(p[1])
            it = next((x for x in DEFAULT_GOLDSHOP if x["id"] == iid), None)
            if not it:
                return self.bot.pm(eid, f"{COL_ERR}Item not found.{COL_END}")
            if pdata["gold"] < it["price"]:
                return self.bot.pm(eid, f"{COL_ERR}Not enough gold.{COL_END}")
            new_gold = pdata["gold"] - it["price"]
            update_balance(self.bot.conn, eos, self.bot.server_id, gold=new_gold)
            self.bot.send(f"giveplus {eid} {it['name']} {it['amount']}")
            self.bot.pm(eid, f"{COL_OK}Purchased {it['friendly']} with gold!{COL_END}")

        # ---------------- Kits ----------------
        elif msg == "/starterkit":
            if pdata["starter_used"]:
                return self.bot.pm(eid, f"{COL_WARN}Already claimed starter kit.{COL_END}")
            for i in STARTER_PACK:
                self.bot.send(f"giveplus {eid} {i['name']} {i['amount']}")
            update_field(self.bot.conn, eos, self.bot.server_id, "starter_used", 1)
            self.bot.pm(eid, f"{COL_OK}Starter kit claimed!{COL_END}")

        elif msg == "/donor":
            donor = pdata.get("donor", None)
            if not donor or donor not in DONOR_TIERS:
                return self.bot.pm(eid, f"{COL_WARN}No donor tier found.{COL_END}")
            for i in DONOR_PACK:
                self.bot.send(f"giveplus {eid} {i['name']} {i['amount']}")
            self.bot.pm(eid, f"{COL_OK}Donor pack delivered! Tier: {donor}{COL_END}")

        elif msg == "/gimme":
            now = time.time()
            last = pdata["last_gimme"] or 0
            if now - last < 6 * 3600:
                return self.bot.pm(eid, f"{COL_WARN}Cooldown active.{COL_END}")
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

        elif msg == "/soil":
            self.bot.send(f"giveplus {eid} terrTopSoil 300")
            self.bot.pm(eid, f"{COL_OK}You received 300 Top Soil!{COL_END}")

        # ---------------- Teleports ----------------
        elif msg.startswith("/settp"):
            p = shlex.split(msg)
            if len(p) < 2:
                return self.bot.pm(eid, f"{COL_INFO}Usage: /settp <name>{COL_END}")
            tpname = p[1].lower()
            pos = self.bot.online.get(eid, {}).get("pos")
            if not pos:
                return self.bot.pm(eid, f"{COL_ERR}Unable to determine your position right now.{COL_END}")
            add_teleport(self.bot.conn, pdata["id"], tpname, pos)
            self.bot.pm(eid, f"{COL_OK}Teleport '{tpname}' saved at {pos}.{COL_END}")

        elif msg == "/tplist":
            tps = get_teleports(self.bot.conn, pdata["id"])
            if not tps:
                return self.bot.pm(eid, f"{COL_INFO}No teleports saved.{COL_END}")
            for tp in tps:
                self.bot.pm(eid, f"{COL_GOLD}{tp['name']}{COL_END} -> ({tp['x']}, {tp['y']}, {tp['z']})")

        elif msg.startswith("/deltp"):
            p = shlex.split(msg)
            if len(p) < 2:
                return self.bot.pm(eid, f"{COL_INFO}Usage: /deltp <name>{COL_END}")
            del_teleport(self.bot.conn, pdata["id"], p[1].lower())
            self.bot.pm(eid, f"{COL_OK}Teleport '{p[1]}' deleted.{COL_END}")

        elif msg.startswith("/tp"):
            p = shlex.split(msg)
            if len(p) < 2:
                return self.bot.pm(eid, f"{COL_INFO}Usage: /tp <name>{COL_END}")
            tpname = p[1].lower()
            tps = get_teleports(self.bot.conn, pdata["id"])
            tp = next((t for t in tps if t["name"].lower() == tpname), None)
            if not tp:
                return self.bot.pm(eid, f"{COL_ERR}Teleport not found.{COL_END}")

            def delayed():
                time.sleep(5)
                x, y, z = int(float(tp["x"])), int(float(tp["y"])), int(float(tp["z"]))
                self.bot.send(f"teleportplayer {eid} {x} {y} {z}")
                self.bot.pm(eid, f"{COL_GOLD}Teleported to '{tpname}' at ({x}, {y}, {z}).{COL_END}")
                self.bot.send(f"getdrone {eid}")

            self.bot.pm(eid, f"{COL_INFO}Teleporting to '{tpname}' in 5 seconds...{COL_END}")
            threading.Thread(target=delayed, daemon=True).start()

        elif msg == "/beammeupscotty":
            x, y, z = random.randint(-2000, 2000), 200, random.randint(-2000, 2000)
            self.bot.send(f"teleportplayer {eid} {x} {y} {z}")
            self.bot.pm(eid, f"{COL_INFO}Beamed up to the sky at ({x}, {y}, {z})!{COL_END}")

        # ---------------- Vehicle recall ----------------
        elif msg.startswith("/findbike"):
            self.bot.send(f"getbike {eid}")
        elif msg.startswith("/find4x4"):
            self.bot.send(f"get4x4 {eid}")
        elif msg.startswith("/findgyro"):
            self.bot.send(f"getgyrocopter {eid}")
        elif msg.startswith("/finddrone"):
            self.bot.send(f"getdrone {eid}")

        # ---------------- Admin ----------------
        elif msg.startswith("/addcoins"):
            if not is_admin(self.bot.conn, eos):
                return self.bot.pm(eid, f"{COL_ERR}Not admin.{COL_END}")
            p = shlex.split(msg)
            if len(p) < 3:
                return
            target_name, amt = p[1], int(p[2])
            teid, target = self._find_online_by_name(target_name.lower())
            if not target:
                return self.bot.pm(eid, f"{COL_ERR}Target not online.{COL_END}")
            tdata = get_player(self.bot.conn, target["eos"], self.bot.server_id)
            update_balance(self.bot.conn, target["eos"], self.bot.server_id, coins=tdata["coins"] + amt)
            self.bot.pm(eid, f"{COL_OK}Added {amt} coins to {target_name}.{COL_END}")

        elif msg.startswith("/removecoins"):
            if not is_admin(self.bot.conn, eos):
                return self.bot.pm(eid, f"{COL_ERR}Not admin.{COL_END}")
            p = shlex.split(msg)
            if len(p) < 3:
                return
            target_name, amt = p[1], int(p[2])
            teid, target = self._find_online_by_name(target_name.lower())
            if not target:
                return self.bot.pm(eid, f"{COL_ERR}Target not online.{COL_END}")
            tdata = get_player(self.bot.conn, target["eos"], self.bot.server_id)
            new_coins = max(0, tdata["coins"] - amt)
            update_balance(self.bot.conn, target["eos"], self.bot.server_id, coins=new_coins)
            self.bot.pm(eid, f"{COL_OK}Removed {amt} coins from {target_name}.{COL_END}")

        elif msg.startswith("/addgold"):
            if not is_admin(self.bot.conn, eos):
                return self.bot.pm(eid, f"{COL_ERR}Not admin.{COL_END}")
            p = shlex.split(msg)
            if len(p) < 3:
                return
            target_name, amt = p[1], int(p[2])
            teid, target = self._find_online_by_name(target_name.lower())
            if not target:
                return self.bot.pm(eid, f"{COL_ERR}Target not online.{COL_END}")
            tdata = get_player(self.bot.conn, target["eos"], self.bot.server_id)
            update_balance(self.bot.conn, target["eos"], self.bot.server_id, gold=tdata["gold"] + amt)
            self.bot.pm(eid, f"{COL_OK}Added {amt} gold to {target_name}.{COL_END}")

        elif msg.startswith("/removegold"):
            if not is_admin(self.bot.conn, eos):
                return self.bot.pm(eid, f"{COL_ERR}Not admin.{COL_END}")
            p = shlex.split(msg)
            if len(p) < 3:
                return
            target_name, amt = p[1], int(p[2])
            teid, target = self._find_online_by_name(target_name.lower())
            if not target:
                return self.bot.pm(eid, f"{COL_ERR}Target not online.{COL_END}")
            tdata = get_player(self.bot.conn, target["eos"], self.bot.server_id)
            new_gold = max(0, tdata["gold"] - amt)
            update_balance(self.bot.conn, target["eos"], self.bot.server_id, gold=new_gold)
            self.bot.pm(eid, f"{COL_OK}Removed {amt} gold from {target_name}.{COL_END}")

        elif msg.startswith("/adddonor"):
            if not is_admin(self.bot.conn, eos):
                return self.bot.pm(eid, f"{COL_ERR}Not admin.{COL_END}")
            p = msg.split()
            if len(p) < 3:
                return self.bot.pm(eid, f"{COL_INFO}Usage: /adddonor <playername> <tier>{COL_END}")
            target_name, tier = p[1], p[2].lower()
            if tier not in DONOR_TIERS:
                return self.bot.pm(eid, f"{COL_ERR}Invalid donor tier. Available: {', '.join(DONOR_TIERS.keys())}{COL_END}")
            teid, target = self._find_online_by_name(target_name.lower())
            if not target:
                return self.bot.pm(eid, f"{COL_ERR}Target not online.{COL_END}")

            tdata = get_player(self.bot.conn, target["eos"], self.bot.server_id)
            tierinfo = DONOR_TIERS[tier]
            new_coins = tdata["coins"] + tierinfo.get("coins", 0)
            new_gold = tdata["gold"] + tierinfo.get("gold", 0)
            update_balance(self.bot.conn, target["eos"], self.bot.server_id, coins=new_coins, gold=new_gold)
            update_field(self.bot.conn, target["eos"], self.bot.server_id, "multiplier", tierinfo.get("multiplier", 1.0))
            update_field(self.bot.conn, target["eos"], self.bot.server_id, "donor", tier)

            # Notify player + admin
            self.bot.pm(teid, f"{COL_OK}You have been granted Donor Tier {tier.upper()}!{COL_END}")
            self.bot.pm(teid, f"{COL_GOLD}+{tierinfo.get('coins',0)} coins, +{tierinfo.get('gold',0)} gold, Multiplier set to x{tierinfo.get('multiplier',1.0)}{COL_END}")
            self.bot.pm(teid, f"{COL_INFO}Use /donor to claim your donor pack.{COL_END}")
            self.bot.pm(eid, f"{COL_OK}{target_name} is now a Donor {tier.upper()}.{COL_END}")

        elif msg.startswith("/removedonor"):
            if not is_admin(self.bot.conn, eos):
                return self.bot.pm(eid, f"{COL_ERR}Not admin.{COL_END}")
            p = msg.split()
            if len(p) < 2:
                return self.bot.pm(eid, f"{COL_INFO}Usage: /removedonor <playername>{COL_END}")
            target_name = p[1]
            teid, target = self._find_online_by_name(target_name.lower())
            if not target:
                return self.bot.pm(eid, f"{COL_ERR}Target not online.{COL_END}")
            update_field(self.bot.conn, target["eos"], self.bot.server_id, "donor", "None")
            update_field(self.bot.conn, target["eos"], self.bot.server_id, "multiplier", 1.0)
            self.bot.pm(teid, f"{COL_WARN}Your donor status has been revoked.{COL_END}")
            self.bot.pm(eid, f"{COL_OK}{target_name}'s donor status removed.{COL_END}")

        elif msg.startswith("/checkplayer"):
            if not is_admin(self.bot.conn, eos):
                return self.bot.pm(eid, f"{COL_ERR}Not admin.{COL_END}")
            p = msg.split()
            if len(p) < 2:
                return self.bot.pm(eid, f"{COL_INFO}Usage: /checkplayer <playername>{COL_END}")
            target_name = p[1].lower()
            teid, target = self._find_online_by_name(target_name)
            if not target:
                return self.bot.pm(eid, f"{COL_ERR}Target not online.{COL_END}")
            pp = get_player(self.bot.conn, target["eos"], self.bot.server_id)
            donor = pp.get("donor", "None")
            mult = pp.get("multiplier", 1.0)
            coins = pp.get("coins", 0)
            gold = pp.get("gold", 0)
            streak = pp.get("streak", 0)
            last_daily = pp.get("last_daily", 0)
            last_gimme = pp.get("last_gimme", 0)
            self.bot.pm(eid, f"{COL_INFO}--- Player Info: {target_name} ---{COL_END}")
            self.bot.pm(eid, f"Coins: {coins}, Gold: {gold}, Mult: x{mult}, Donor: {donor}")
            self.bot.pm(eid, f"Streak: {streak}, Last Daily: {last_daily}, Last Gimme: {last_gimme}")

        elif msg.startswith("/clearpackuse"):
            if not is_admin(self.bot.conn, eos):
                return self.bot.pm(eid, f"{COL_ERR}Not admin.{COL_END}")

            # Accept either order: /clearpackuse <player> [starterkit|donor|both]
            # or:                    /clearpackuse [starterkit|donor|both] <player>
            toks = msg.split()
            if len(toks) < 2:
                return self.bot.pm(eid, f"{COL_INFO}Usage: /clearpackuse <playername> [starterkit|donor|both]{COL_END}")

            args = [a.lower() for a in toks[1:]]
            mode = "both"
            # find mode
            for m in ("starterkit", "donor", "both"):
                if m in args:
                    mode = m
                    args.remove(m)
                    break
            if not args:
                return self.bot.pm(eid, f"{COL_INFO}Usage: /clearpackuse <playername> [starterkit|donor|both]{COL_END}")
            target_name = args[0]

            teid, target = self._find_online_by_name(target_name.lower())
            if not target:
                return self.bot.pm(eid, f"{COL_ERR}Target not online.{COL_END}")

            if mode in ("starterkit", "both"):
                update_field(self.bot.conn, target["eos"], self.bot.server_id, "starter_used", 0)
            if mode in ("donor", "both"):
                update_field(self.bot.conn, target["eos"], self.bot.server_id, "donor", "None")
                update_field(self.bot.conn, target["eos"], self.bot.server_id, "multiplier", 1.0)

            self.bot.pm(eid, f"{COL_OK}Cleared pack usage for {target_name} ({mode}).{COL_END}")

        elif msg.startswith("/addadmin"):
            p = shlex.split(msg)
            # bootstrap via master password
            if len(p) == 2:
                password = p[1]
                master_pw = get_master_password(self.bot.conn)
                if master_pw and password == master_pw:
                    add_admin(self.bot.conn, eos)
                    return self.bot.pm(eid, f"{COL_OK}{name} promoted to Admin using master password!{COL_END}")
                else:
                    return self.bot.pm(eid, f"{COL_ERR}Invalid master password.{COL_END}")
            return self.bot.pm(eid, f"{COL_INFO}Usage: /addadmin <masterpassword>{COL_END}")

        elif msg.startswith("/adminadd"):
            if not is_admin(self.bot.conn, eos):
                return self.bot.pm(eid, f"{COL_ERR}Not admin.{COL_END}")
            p = shlex.split(msg)
            if len(p) < 2:
                return self.bot.pm(eid, f"{COL_INFO}Usage: /addadmins <playername>{COL_END}")
            target_name = p[1]
            teid, target = self._find_online_by_name(target_name.lower())
            if not target:
                return self.bot.pm(eid, f"{COL_ERR}Target not online.{COL_END}")
            add_admin(self.bot.conn, target["eos"])
            self.bot.pm(eid, f"{COL_OK}{target_name} is now admin.{COL_END}")

        # ---------------- Vote ----------------
        elif msg == "/vote":
            api_key = "HgpNQra3gAUGmzYL6SDCV30YNuFUSzGniRy"
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

