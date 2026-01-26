CREATE TABLE IF NOT EXISTS vat_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    period_code TEXT NOT NULL,

    kz81 REAL DEFAULT 0,
    kz86 REAL DEFAULT 0,
    kz43 REAL DEFAULT 0,
    kz89 REAL DEFAULT 0,
    kz61 REAL DEFAULT 0,

    calculated_vat REAL DEFAULT 0,
    status TEXT DEFAULT 'draft',

    UNIQUE (client_id, year, period_code),
    FOREIGN KEY (client_id) REFERENCES clients(id)
);
