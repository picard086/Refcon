#!/usr/bin/env python3
import time
from economy import EconomyBot
from config import load_server_config

def main():
    print("[econ] Starting Refuge Economy Bot...", flush=True)

    # Load server config from DB
    server = load_server_config()
    print(f"[econ] Loaded server config: {server['name']} {server['ip']}:{server['port']}", flush=True)

    # Start the bot
    bot = EconomyBot(server)
    bot.run()  # should block if implemented correctly

    # Safety net: if run() ever returns, keep process alive
    print("[econ] WARNING: bot.run() exited unexpectedly, keeping process alive.", flush=True)
    while True:
        time.sleep(60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[econ] Fatal error: {e}", flush=True)
        raise
