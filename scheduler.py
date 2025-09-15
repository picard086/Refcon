import threading, time
from db import get_conn, get_player, update_balance

def start_income_loop(bot):
    def loop():
        while True:
            time.sleep(60)
            conn = get_conn()
            cur = conn.execute("SELECT eos, coins, multiplier FROM players WHERE server_id=?", (bot.server_id,))
            for row in cur.fetchall():
                new_coins = row["coins"] + int(1 * row["multiplier"])
                update_balance(conn, row["eos"], bot.server_id, coins=new_coins)
    threading.Thread(target=loop, daemon=True).start()
