from fastapi import Response, HTTPException
from backend.elster_xml.ustva import generate_ustva_xml
from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import sqlite3
app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.db"

def get_db():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL UNIQUE,
            street TEXT NOT NULL,
            street_number TEXT NOT NULL,
            postcode TEXT NOT NULL,
            city TEXT NOT NULL,
            tax_number TEXT NOT NULL,
            vat_id TEXT
        )
    """)

    cur.execute("""
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
        )
    """)

    conn.commit()
    conn.close()


@app.on_event("startup")
def startup():
    init_db()


# ---------- MODELS ----------
class ClientIn(BaseModel):
    company_name: str
    street: str
    street_number: str
    postcode: str
    city: str
    tax_number: str
    vat_id: str | None = None


from pydantic import BaseModel, validator

class VatReportIn(BaseModel):
    client_id: int
    year: int
    period_code: str

    kz81: float = 0
    kz86: float = 0
    kz43: float = 0
    kz89: float = 0
    kz61: float = 0

    @validator("period_code")
    def validate_period_code(cls, v):
        allowed = {f"{i:02d}" for i in range(1, 13)} | {"41", "42", "43", "44"}
        if v not in allowed:
            raise ValueError("Invalid Zeitraum. Allowed: 01–12 or 41–44")
        return v

# ---------- CLIENTS ----------
@app.post("/clients")
def create_client(data: ClientIn):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO clients (
            company_name, street, street_number,
            postcode, city, tax_number, vat_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data.company_name,
        data.street,
        data.street_number,
        data.postcode,
        data.city,
        data.tax_number,
        data.vat_id
    ))
    conn.commit()
    conn.close()
    return {"status": "client_created"}


@app.get("/clients")
def list_clients():
    conn = get_db()
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT id, company_name, street, street_number,
               postcode, city, tax_number, vat_id
        FROM clients
    """).fetchall()

    conn.close()

    return [
        {
            "id": r[0],
            "company_name": r[1],
            "street": r[2],
            "street_number": r[3],
            "postcode": r[4],
            "city": r[5],
            "tax_number": r[6],
            "vat_id": r[7],
        }
        for r in rows
    ]


@app.get("/clients/search")
def search_clients(q: str):
    conn = get_db()
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT id, company_name
        FROM clients
        WHERE company_name LIKE ?
        ORDER BY company_name
        LIMIT 10
    """, (f"%{q}%",)).fetchall()

    conn.close()

    return [
        {"id": r[0], "company_name": r[1]}
        for r in rows
    ]


# ---------- VAT REPORTS ----------
@app.post("/vat-reports")
def create_vat_report(data: VatReportIn):
    calculated_vat = (
        data.kz81 * 0.19 +
        data.kz86 * 0.07 +
        data.kz89 -
        data.kz61
    )

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO vat_reports (
                client_id, year, period_code,
                kz81, kz86, kz43, kz89, kz61, calculated_vat
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.client_id,
            data.year,
            data.period_code,
            data.kz81,
            data.kz86,
            data.kz43,
            data.kz89,
            data.kz61,
            calculated_vat
        ))
        conn.commit()

        vat_report_id = cur.lastrowid
        created = True

    except sqlite3.IntegrityError:
        # VAT report already exists → fetch it
        row = cur.execute("""
            SELECT id, calculated_vat
            FROM vat_reports
            WHERE client_id = ? AND year = ? AND period = ?
        """, (
            data.client_id,
            data.year,
            data.period_code
        )).fetchone()

        vat_report_id = row[0]
        calculated_vat = row[1]
        created = False

    finally:
        conn.close()

    return {
        "id": vat_report_id,
        "created": created,
        "calculated_vat": calculated_vat
    }



@app.get("/vat-reports")
def list_vat_reports():
    conn = get_db()
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT
            v.id,
            c.company_name,
            v.year,
            v.period_code,
            v.kz81,
            v.kz86,
            v.kz43,
            v.kz89,
            v.kz61,
            v.calculated_vat,
            v.status
        FROM vat_reports v
        JOIN clients c ON c.id = v.client_id
    """).fetchall()

    conn.close()
    return rows

@app.get("/vat-reports/{vat_report_id}/xml")
def get_vat_report_xml(vat_report_id: int):
    try:
        xml = generate_ustva_xml(vat_report_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return Response(
        content=xml,
        media_type="application/xml; charset=utf-8"
    )
