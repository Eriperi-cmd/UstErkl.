# backend/elster_xml/ustva.py

import sqlite3
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "database.db"


def generate_ustva_xml(vat_report_id: int) -> str:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    row = cur.execute("""
        SELECT
            c.company_name,
            c.street,
            c.street_number,
            c.city,
            c.postcode,
            v.year,
            v.period_code,
            v.kz81,
            v.kz86,
            v.kz43,
            v.kz89,
            v.kz61
        FROM vat_reports v
        JOIN clients c ON c.id = v.client_id
        WHERE v.id = ?
    """, (vat_report_id,)).fetchone()

    conn.close()

    if not row:
        raise ValueError("VAT report not found")

    (
        company_name,
        street,
        street_number,
        city,
        postcode,
        year,
        period_code,
        kz81,
        kz86,
        kz43,
        kz89,
        kz61
    ) = row

    # ---------- XML ----------
    root = ET.Element("Elster")

    ET.SubElement(root, "Erstellungsdatum").text = date.today().strftime("%Y%m%d")
    ET.SubElement(root, "Bezeichnung").text = company_name

    unternehmer = ET.SubElement(root, "Unternehmer")
    ET.SubElement(unternehmer, "Str").text = street
    ET.SubElement(unternehmer, "Hausnummer").text = street_number
    ET.SubElement(unternehmer, "Ort").text = city
    ET.SubElement(unternehmer, "PLZ").text = postcode
    ET.SubElement(unternehmer, "Land").text = "Spanien"

    ustva = ET.SubElement(root, "Umsatzsteuervoranmeldung")
    ET.SubElement(ustva, "Jahr").text = str(year)
    ET.SubElement(ustva, "Zeitraum").text = period_code

    # ---------- KENNZIFFERN ----------
    if kz81:
        ET.SubElement(ustva, "Kz81").text = f"{kz81:.2f}"
    if kz86:
        ET.SubElement(ustva, "Kz86").text = f"{kz86:.2f}"
    if kz43:
        ET.SubElement(ustva, "Kz43").text = f"{kz43:.2f}"
    if kz89:
        ET.SubElement(ustva, "Kz89").text = f"{kz89:.2f}"
    if kz61:
        ET.SubElement(ustva, "Kz61").text = f"{kz61:.2f}"

    return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")
