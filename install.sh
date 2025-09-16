#!/bin/bash
set -e

echo "=== Refuge Economy Bot Installer ==="

# --- Ask for master password ---
read -sp "Set Master Admin Password: " MASTER_PASS
echo

# --- Ask how many servers ---
read -p "How many servers do you want to configure? " SERVER_COUNT

# --- Always make sure sqlite3 is installed ---
sudo apt update
sudo apt install -y sqlite3

# --- Install Python 3.12.3 if missing ---
if ! python3.12 --version &>/dev/null; then
  echo "Installing Python 3.12.3..."
  sudo apt install -y wget build-essential libssl-dev zlib1g-dev \
    libncurses5-dev libncursesw5-dev libreadline-dev libsqlite3-dev \
    libgdbm-dev libdb5.3-dev libbz2-dev libexpat1-dev liblzma-dev tk-dev uuid-dev
  wget https://www.python.org/ftp/python/3.12.3/Python-3.12.3.tgz
  tar xvf Python-3.12.3.tgz
  cd Python-3.12.3
  ./configure --enable-optimizations
  make -j$(nproc)
  sudo make altinstall
  cd ..
  rm -rf Python-3.12.3 Python-3.12.3.tgz
fi

# --- Set up venv ---
cd "$(dirname "$0")"
sudo apt install -y python3.12-venv
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install requests pytz fastapi uvicorn

# --- Init database ---
if [ ! -f economy.db ]; then
  echo "Initializing database schema..."
  sqlite3 economy.db < schema.sql
else
  echo "Database already exists, checking schema..."

  # Make sure "name" column exists in servers
  HAS_NAME=$(sqlite3 economy.db "PRAGMA table_info(servers);" | awk -F'|' '{print $2}' | grep -c '^name$')
  if [ "$HAS_NAME" -eq 0 ]; then
    echo "Adding 'name' column to servers table..."
    sqlite3 economy.db "ALTER TABLE servers ADD COLUMN name TEXT DEFAULT 'Unnamed';"
  fi
fi

# --- Insert servers ---
for ((i=1; i<=SERVER_COUNT; i++)); do
  echo "---- Configuring Server $i ----"
  read -p "Server Name: " SERVER_NAME
  read -p "Server IP: " SERVER_IP
  read -p "RCON Port: " SERVER_PORT
  read -sp "RCON Password: " SERVER_PASS
  echo
  sqlite3 economy.db <<EOF
INSERT INTO servers (name, ip, port, password)
VALUES ("$SERVER_NAME", "$SERVER_IP", $SERVER_PORT, "$SERVER_PASS");
EOF
done

# --- Store master password in settings table ---
sqlite3 economy.db <<EOF
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
DELETE FROM settings WHERE key='master_password';
INSERT INTO settings (key, value) VALUES ('master_password', "$MASTER_PASS");
EOF

# --- Always seed WebAdmin as permanent admin ---
sqlite3 economy.db <<EOF
CREATE TABLE IF NOT EXISTS admins (eos TEXT PRIMARY KEY);
INSERT OR IGNORE INTO admins (eos) VALUES ("WebAdmin");
EOF

# --- Create systemd service ---
SERVICE_FILE=/etc/systemd/system/refconbot.service
sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=Refuge Economy Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python $(pwd)/__main__.py
Restart=always

[Install]
WantedBy=multi-user.target
EOL

sudo systemctl daemon-reload
sudo systemctl enable refconbot.service
sudo systemctl restart refconbot.service

echo "=== Refuge Economy Bot installed and running ==="
