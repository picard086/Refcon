# Refcon Server Manager

A custom **7 Days to Die Economy Bot** that connects to your server via **Telnet**, tracks players, manages coins & gold, provides in-game shops, kits, teleports, and integrates with voting sites.  

Built for the **Refuge Gaming Cluster** but easily adaptable for other servers.  

---

## ✨ Features

- 🎮 Player economy with **coins** and **gold** balances  
- 🛒 In-game **/shop** and **/goldshop** with configurable items  
- 🎁 **Starter kit**, **daily rewards**, and **/gimme** random drops  
- 📌 **Teleport system** (`/settp`, `/tplist`, `/tp`)  
- 🛡️ **Admin tools** (`/addcoins`, `/addadmins`)  
- 📢 **Vote rewards** via [7daystodie-servers.com](https://7daystodie-servers.com/) API  
- 🔗 SQLite backend for persistence  

---

## ⚡ Requirements

- Python 3.10+  
- A running **7 Days to Die Dedicated Server** with **Telnet enabled**  
- Git + virtualenv (recommended)  

---

## 🚀 Installation

Clone the repo and install dependencies:

```bash
git clone https://github.com/picard086/Refcon.git
cd Refcon
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Set up the economy database:

```bash
./install.sh
```

---

## ▶️ Running

Manual run:

```bash
./venv/bin/python __main__.py
```

Or via systemd (Linux service):

```bash
sudo systemctl enable refconbot
sudo systemctl start refconbot
```

Logs:

```bash
journalctl -u refconbot -f
```

---

## 💬 Player Commands

| Command         | Description |
|-----------------|-------------|
| `/ping`         | Test the bot (responds with `pong`) |
| `/balance`      | Show your Refuge Coins balance |
| `/goldbalance`  | Show your Refuge Gold balance |
| `/shop`         | List items available for Refuge Coins |
| `/buy <id>`     | Buy an item from the shop |
| `/goldshop`     | List items available for Refuge Gold |
| `/goldbuy <id>` | Buy an item from the gold shop |
| `/starterkit`   | Claim your one-time starter kit |
| `/gimme`        | Claim a random item every 6 hours |
| `/daily`        | Claim daily Refuge Coins |
| `/settp <name>` | Save a personal teleport point |
| `/tplist`       | List saved teleports |
| `/tp <name>`    | Teleport to a saved point |
| `/deltp <name>` | Delete a saved teleport |
| `/vote`         | Claim voting rewards |

---

## 🔧 Admin Commands

| Command                  | Description |
|--------------------------|-------------|
| `/addcoins <player> <x>` | Add coins to a player |
| `/addadmins <player>`    | Promote a player to admin |

---

## ⚙️ Configuration

- **Shops** are hardcoded in `constants.py` (`DEFAULT_SHOP` and `DEFAULT_GOLDSHOP`)  
- **Donor tiers** and multipliers also live in `constants.py`  
- **Database** is `economy.db` (SQLite)  
- **Admins** can be loaded from the DB (`admins` table)  

---

## 🗂 Project Structure

```
Refcon/
│── economy.py        # Main bot runner
│── commands.py       # Command handling
│── constants.py      # Shop items, donor tiers, rewards
│── utils.py          # Logging, colors, admin loader
│── db.py             # SQLite helpers
│── scheduler.py      # Task scheduling (daily/gimme timers)
│── install.sh        # DB setup script
│── refuge_data/      # JSON / data storage
```

---

## 📜 License

MIT License – feel free to fork and adapt for your own servers.  
Credit appreciated to **Refuge Gaming**.
