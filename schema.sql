CREATE TABLE servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    ip TEXT,
    port INTEGER,
    password TEXT
);

CREATE TABLE players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id INTEGER,
    eos TEXT,
    name TEXT,
    coins INTEGER DEFAULT 0,
    gold INTEGER DEFAULT 0,
    multiplier REAL DEFAULT 1.0,
    donor TEXT,
    donor_used BOOLEAN DEFAULT 0,
    starter_used BOOLEAN DEFAULT 0,
    streak INTEGER DEFAULT 0,
    last_daily INTEGER DEFAULT 0,
    last_gimme INTEGER DEFAULT 0,
    FOREIGN KEY (server_id) REFERENCES servers(id)
);

CREATE TABLE teleports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER,
    name TEXT,
    x REAL, y REAL, z REAL,
    FOREIGN KEY (player_id) REFERENCES players(id)
);

CREATE TABLE shops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT,
    item_name TEXT,
    friendly TEXT,
    price INTEGER,
    amount INTEGER
);

CREATE TABLE admins (
    eos TEXT PRIMARY KEY
);

CREATE TABLE votes (
    eos TEXT PRIMARY KEY,
    last_vote INTEGER
);
