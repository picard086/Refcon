import threading
import time
from db import get_conn, update_balance


class Scheduler:
    def __init__(self, bot, income_interval=60, lp_interval=30):
        self.bot = bot
        self.income_interval = income_interval
        self.lp_interval = lp_interval
        self.running = False
        self.income_thread = None
        self.lp_thread = None

    def _income_loop(self):
        while self.running:
            time.sleep(self.income_interval)
            if not self.running:
                break
            try:
                conn = self.bot.conn or get_conn()
                cur = conn.execute(
                    "SELECT eos, coins, multiplier FROM players WHERE server_id=?",
                    (self.bot.server_id,),
                )
                for row in cur.fetchall():
                    new_coins = row["coins"] + int(1 * row["multiplier"])
                    update_balance(conn, row["eos"], self.bot.server_id, coins=new_coins)
            except Exception as e:
                print(f"[econ][Scheduler] income error: {e}")

    def _lp_loop(self):
        while self.running:
            time.sleep(self.lp_interval)
            if not self.running:
                break
            try:
                self.bot.send("lp")
            except Exception as e:
                print(f"[econ][Scheduler] lp error: {e}")

    def start(self):
        """Start both loops in background threads."""
        if not self.running:
            self.running = True
            self.income_thread = threading.Thread(target=self._income_loop, daemon=True)
            self.lp_thread = threading.Thread(target=self._lp_loop, daemon=True)
            self.income_thread.start()
            self.lp_thread.start()

    def stop(self):
        """Stop both loops."""
        self.running = False
        if self.income_thread:
            self.income_thread.join(timeout=2)
            self.income_thread = None
        if self.lp_thread:
            self.lp_thread.join(timeout=2)
            self.lp_thread = None

    def run_pending(self):
        """Compatibility: just ensure scheduler is started."""
        if not self.running:
            self.start()
