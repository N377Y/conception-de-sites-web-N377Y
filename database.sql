
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    mail TEXT NOT NULL,
    name TEXT NOT NULL,
    profile_picture TEXT
);

CREATE TABLE games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gameCode TEXT NOT NULL,
    player1_id TEXT,
    player2_id TEXT,
    state TEXT NOT NULL  -- waiting, ready, started, ended
);