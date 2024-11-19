
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    mail TEXT NOT NULL,
    name TEXT NOT NULL,
    profile_picture TEXT
);