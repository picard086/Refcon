#!/usr/bin/env python3
import sys
from config import load_server_config
from telnet_client import TelnetBot

def main():
    server = load_server_config()
    bot = TelnetBot(
        host=server["ip"],
        port=server["port"],
        password=server["password"],
        server_id=server["id"]
    )
    bot.connect()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
