
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
    player1_username TEXT,
    player2_id TEXT,
    player2_username TEXT,
    state TEXT NOT NULL,  -- waiting, started, ended
    score1 INTEGER DEFAULT 0,
    score2 INTEGER DEFAULT 0,
    FOREIGN KEY (player1_id) REFERENCES users(id),
    FOREIGN KEY (player2_id) REFERENCES users(id)
);