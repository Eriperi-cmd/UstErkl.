@app.get("/clients")
def list_clients():
    conn = get_db()
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT
            id,
            company_name,
            street,
            street_number,
            postcode,
            city,
            tax_number,
            vat_id
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
