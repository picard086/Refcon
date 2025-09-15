import threading
import time
from db import get_conn, update_balance


class Scheduler:
    def __init__(self, bot, interval=60):
        self.bot = bot
        self.interval = interval
        self.running = False
        self.thread = None

    def _income_loop(self):
        while self.running:
            time.sleep(self.interval)
            conn = get_conn()
            cur = conn.execute(
                "SELECT eos, coins, multiplier FROM players WHERE server_id=?",
                (self.bot.server_id,)
            )
            for row in cur.fetchall():
                new_coins = row["coins"] + int(1 * row["multiplier"])
                update_balance(conn, row["eos"], self.bot.server_id, coins=new_coins)

    def start(self):
        """Start the income loop in a background thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._income_loop, daemon=True)
            self.thread.start()

    def stop(self):
        """Stop the scheduler loop."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
            self.thread = None

    def run_pending(self):
        """Compatibility: just ensure scheduler is started."""
        if not self.running:
            self.start()

