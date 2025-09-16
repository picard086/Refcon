import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import requests

# Config
DB_PATH = "economy.db"
BOT_API_URL = "http://127.0.0.1:8899/run_command"  # bot will expose this later

app = FastAPI(title="RefconBot Web Panel", version="0.1")

# ---- Models ----
class DonorRequest(BaseModel):
    player: str
    tier: str

class BalanceRequest(BaseModel):
    player: str
    coins: int = 0
    gold: int = 0

# ---- Helpers ----
def query_db(query, args=(), one=False):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.execute(query, args)
    rv = cur.fetchall()
    con.commit()
    con.close()
    return (rv[0] if rv else None) if one else rv

# ---- Endpoints ----
@app.get("/players")
def get_players():
    rows = query_db("SELECT id, name, coins, gold, donor FROM players;")
    return [dict(row) for row in rows]

@app.post("/donor")
def set_donor(req: DonorRequest):
    query_db("UPDATE players SET donor = ? WHERE name = ?;", (req.tier, req.player))
    # notify bot so it tells the player in-game
    try:
        requests.post(BOT_API_URL, json={"cmd": f"/adddonor {req.player} {req.tier}"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bot notification failed: {e}")
    return {"status": "ok", "player": req.player, "tier": req.tier}

@app.post("/balance")
def set_balance(req: BalanceRequest):
    query_db("UPDATE players SET coins = ?, gold = ? WHERE name = ?;", (req.coins, req.gold, req.player))
    return {"status": "ok", "player": req.player, "coins": req.coins, "gold": req.gold}

# ---- Main ----
if __name__ == "__main__":
    uvicorn.run("webserver:app", host="0.0.0.0", port=8848, reload=True)
