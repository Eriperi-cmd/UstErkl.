CREATE TABLE IF NOT EXISTS periods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    period_code TEXT NOT NULL,
    quarter INTEGER,
    UNIQUE (client_id, year, period_code, quarter),
    FOREIGN KEY (client_id) REFERENCES clients(id)
);
