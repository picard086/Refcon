#!/bin/bash
set -e

echo "=== Refuge Economy Bot Installer ==="

# --- Ask for server details ---
read -p "Server Name: " SERVER_NAME
read -p "Server IP: " SERVER_IP
read -p "RCON Port: " SERVER_PORT
read -sp "RCON Password: " SERVER_PASS
echo

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
pip install requests pytz

# --- Init database ---
sqlite3 economy.db < schema.sql
sqlite3 economy.db "INSERT INTO servers (name, ip, port, password) VALUES ('$SERVER_NAME','$SERVER_IP',$SERVER_PORT,'$SERVER_PASS');"

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
ExecStart=$(pwd)/venv/bin/python -m __main__
Restart=always

[Install]
WantedBy=multi-user.target
EOL

sudo systemctl daemon-reload
sudo systemctl enable refconbot.service
sudo systemctl start refconbot.service


echo "=== Refuge Economy Bot installed and running ==="
