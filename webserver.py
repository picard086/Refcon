import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import requests
import threading, time

# Config
DB_PATH = "economy.db"
BOT_API_URL = "http://127.0.0.1:8899/run_command"   # bot endpoint for commands
BOT_PLAYERS_URL = "http://127.0.0.1:8899/online_players"

app = FastAPI(title="RefconBot Web Panel", version="0.2")

# ---- Models ----
class DonorRequest(BaseModel):
    player: str
    tier: str   # now supports t1, t2, t3, t4

class BalanceRequest(BaseModel):
    player: str
    coins: int = 0
    gold: int = 0

# ---- DB Helper ----
def query_db(query, args=(), one=False):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.execute(query, args)
    rv = cur.fetchall()
    con.commit()
    con.close()
    return (rv[0] if rv else None) if one else rv

# ---- Global cache for players ----
latest_players = []

def poll_players():
    """Background thread to keep player list fresh from bot API."""
    global latest_players
    while True:
        try:
            res = requests.get(BOT_PLAYERS_URL, timeout=5)
            if res.status_code == 200:
                latest_players = res.json()
        except Exception as e:
            print("Error polling players:", e)
        time.sleep(5)  # refresh interval

# ---- Endpoints ----
@app.get("/players")
def get_players():
    return latest_players

@app.post("/donor")
def set_donor(req: DonorRequest):
    tier = req.tier.lower()
    if tier not in ["t1", "t2", "t3", "t4"]:
        raise HTTPException(status_code=400, detail="Invalid donor tier (use t1, t2, t3, or t4)")

    query_db("UPDATE players SET donor = ? WHERE name = ?;", (tier, req.player))

    # notify bot so it tells the player in-game
    try:
        requests.post(BOT_API_URL, json={"cmd": f"/adddonor {req.player} {tier}"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bot notification failed: {e}")
    return {"status": "ok", "player": req.player, "tier": tier}

@app.post("/balance")
def set_balance(req: BalanceRequest):
    query_db(
        "UPDATE players SET coins = ?, gold = ? WHERE name = ?;",
        (req.coins, req.gold, req.player),
    )
    return {
        "status": "ok",
        "player": req.player,
        "coins": req.coins,
        "gold": req.gold,
    }

# ---- Main ----
if __name__ == "__main__":
    # Start background poller before launching API
    threading.Thread(target=poll_players, daemon=True).start()
    uvicorn.run("webserver:app", host="0.0.0.0", port=8848, reload=True)
