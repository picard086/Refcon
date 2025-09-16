# Refcon Server Manager

A custom **7 Days to Die** Economy & Utility Bot that connects via Telnet, tracks players, manages coins & gold, provides in-game shops, kits, teleports, voting integration, and admin tools. Built for Refuge Gaming but fully configurable for any server.  

---

## ✨ Features

**Player Commands**

| Command | Description |
|---|---|
| `/ping` | Test the bot (responds with `pong`) |
| `/balance` | Show your Refuge Coin balance |
| `/goldbalance` | Show your Refuge Gold balance |
| `/shop` | List items available for Refuge Coins |
| `/buy <id>` | Purchase an item from the coin shop |
| `/goldshop` | List items available for Refuge Gold |
| `/goldbuy <id>` | Purchase an item from the gold shop |
| `/starterkit` | Claim your one-time starter kit |
| `/donor` | Claim donor pack if eligible |
| `/gimme` | Random reward every 6 hours |
| `/daily` | Claim daily coin reward (24h cooldown) |
| `/soil` | Get 300 Top Soil |
| `/settp <name>` | Save a personal teleport point |
| `/tplist` | List your saved teleport points |
| `/tp <name>` | Teleport to saved point (5-sec delay) |
| `/deltp <name>` | Delete a saved teleport point |
| `/beammeupscotty` | Random teleport to sky coordinates |
| `/findbike`, `/find4x4`, `/findgyro`, `/finddrone` | Recall lost vehicles |
| `/vote` | Claim rewards via the voting site API |

**Admin Commands**

| Command | Description |
|---|---|
| `/addcoins <player> <amount>` | Add coins to a player |
| `/removecoins <player> <amount>` | Remove coins from a player |
| `/addgold <player> <amount>` | Add gold to a player |
| `/removegold <player> <amount>` | Remove gold from a player |
| `/adddonor <player> <tier>` | Grant a donor tier; gives bonus coins/gold & multiplier |
| `/removedonor <player>` | Remove donor status (reset donor & multiplier) |
| `/checkplayer <player>` | View a player's balances, donor status, and cooldowns |
| `/clearpackuse <player> [starterkit|donor|both]` | Reset the usage of starter/donor pack for the player |
| `/addadmin <masterpassword>` | Bootstrap as an admin using master password |
| `/addadmins <player>` | Promote another player to admin |

---

## ⚙ Requirements

- Python 3.10+  
- 7 Days to Die Dedicated Server with Telnet enabled  
- Git, virtualenv (or Python venv)  
- SQLite (bundled; no external server needed)

---

## 🛠 Installation

Below are the steps to get Refcon running.

```bash
# 1. Clone your repository
git clone https://github.com/picard086/Refcon.git
cd Refcon

# 2. Create & activate Python virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize the database and setup via install script
chmod +x install.sh
./install.sh

# 5. Configure your server details
#    Edit config.py (or config.json if used) to specify:
#      - server host, port, password
#      - server_id, etc.

# 6. (Optional) Setup systemd service
# Create a service file (e.g. refconbot.service) to run:
# venv/bin/python economy.py (or __main__.py, depending on your entrypoint)
# Set it to start on boot, enable, and start.

sudo systemctl enable refconbot
sudo systemctl start refconbot

# 7. Monitor logs
journalctl -u refconbot -f
