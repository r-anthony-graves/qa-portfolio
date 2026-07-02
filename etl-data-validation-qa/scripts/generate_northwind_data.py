"""
Generate Northwind-derived ETL test data for etl-data-validation-qa.

Source schema : Salesforce Accounts + Contacts (CSV)
Target schema : Data Warehouse Accounts + Contacts (CSV)
Basis         : Northwind Customers table (20 real records)

Intentional defects injected (mirrors original test expectations):
  DEF-ETL-001 / DEF-ETL-003 — NW-DRACD, NW-EASTC dropped from warehouse_accounts
  DEF-ETL-005               — Their contacts remain in warehouse_contacts (orphaned FK)

Usage
-----
  cd etl-data-validation-qa
  python scripts/generate_northwind_data.py
"""

import csv
import unicodedata
from datetime import date, timedelta
from pathlib import Path

# ─── Real Northwind Customers ────────────────────────────────────────────────
# (customer_id, company_name, contact_name, contact_title, city, region, country, phone)
NORTHWIND_CUSTOMERS = [
    ("ALFKI", "Alfreds Futterkiste",               "Maria Anders",       "Sales Representative", "Berlin",       "",   "Germany",     "030-0074321"),
    ("ANATR", "Ana Trujillo Emparedados y helados", "Ana Trujillo",       "Owner",                "Mexico D.F.",  "",   "Mexico",      "(5) 555-4729"),
    ("ANTON", "Antonio Moreno Taqueria",            "Antonio Moreno",     "Owner",                "Mexico D.F.",  "",   "Mexico",      "(5) 555-3932"),
    ("AROUT", "Around the Horn",                    "Thomas Hardy",       "Sales Representative", "London",       "UK", "UK",          "(171) 555-7788"),
    ("BERGS", "Berglunds snabbkop",                 "Christina Berglund", "Order Administrator",  "Lulea",        "",   "Sweden",      "0921-12 34 65"),
    ("BLAUS", "Blauer See Delikatessen",             "Hanna Moos",         "Sales Representative", "Mannheim",     "",   "Germany",     "0621-08460"),
    ("BLONP", "Blondesddsl pere et fils",            "Frederique Citeaux", "Marketing Manager",    "Strasbourg",   "",   "France",      "88.60.15.31"),
    ("BOLID", "Bolido Comidas preparadas",           "Martin Sommer",      "Owner",                "Madrid",       "",   "Spain",       "(91) 555 22 82"),
    ("BONAP", "Bon app",                             "Laurence Lebihan",   "Owner",                "Marseille",    "",   "France",      "91.24.45.40"),
    ("BOTTM", "Bottom-Dollar Markets",               "Elizabeth Lincoln",  "Accounting Manager",   "Tsawassen",    "BC", "Canada",      "(604) 555-4729"),
    ("BSBEV", "B's Beverages",                       "Victoria Ashworth",  "Sales Representative", "London",       "UK", "UK",          "(171) 555-1212"),
    ("CACTU", "Cactus Comidas para llevar",          "Patricio Simpson",   "Sales Agent",          "Buenos Aires", "",   "Argentina",   "(1) 135-5555"),
    ("CENTC", "Centro comercial Moctezuma",          "Francisco Chang",    "Marketing Manager",    "Mexico D.F.",  "",   "Mexico",      "(5) 555-3392"),
    ("CHOPS", "Chop-suey Chinese",                   "Yang Wang",          "Owner",                "Bern",         "",   "Switzerland", "0452-076545"),
    ("COMMI", "Comercio Mineiro",                    "Pedro Afonso",       "Sales Associate",      "Sao Paulo",    "SP", "Brazil",      "(11) 555-7647"),
    ("CONSH", "Consolidated Holdings",               "Elizabeth Brown",    "Sales Representative", "London",       "UK", "UK",          "(171) 555-2282"),
    ("DRACD", "Drachenblut Delikatessen",            "Sven Ottlieb",       "Order Administrator",  "Aachen",       "",   "Germany",     "0241-039123"),
    ("DUMON", "Du monde entier",                     "Janine Labrune",     "Owner",                "Nantes",       "",   "France",      "40.67.88.88"),
    ("EASTC", "Eastern Connection",                  "Ann Devon",          "Sales Agent",          "London",       "UK", "UK",          "(171) 555-0297"),
    ("ERNSH", "Ernst Handel",                        "Roland Mendel",      "Sales Manager",        "Graz",         "",   "Austria",     "7675-3425"),
]

# ─── Lookup maps ─────────────────────────────────────────────────────────────
ACCOUNT_TYPE = {
    "Owner":               "SMB",
    "Sales Representative":"Partner",
    "Sales Manager":       "Enterprise",
    "Sales Agent":         "Partner",
    "Marketing Manager":   "Partner",
    "Order Administrator": "Partner",
    "Accounting Manager":  "Enterprise",
    "Sales Associate":     "Partner",
}

INDUSTRY = {
    "Germany":     ("Manufacturing",  "MFG"),
    "Mexico":      ("Food & Beverage","F_B"),
    "UK":          ("Distribution",   "DIST"),
    "Sweden":      ("Retail",         "RETAIL"),
    "France":      ("Food & Beverage","F_B"),
    "Spain":       ("Food & Beverage","F_B"),
    "Canada":      ("Retail",         "RETAIL"),
    "Argentina":   ("Food & Beverage","F_B"),
    "Switzerland": ("Food & Beverage","F_B"),
    "Brazil":      ("Distribution",   "DIST"),
    "Austria":     ("Wholesale",      "WHSL"),
}

REVENUE_BASE = {"SMB": 900_000, "Partner": 3_100_000, "Enterprise": 11_500_000}

LEAD_SOURCES  = ["Referral", "Web", "Trade Show", "Cold Call", "Partner"]
LS_CODE       = {"Referral": "REF", "Web": "WEB", "Trade Show": "TRADE",
                 "Cold Call": "COLD", "Partner": "PARTNER"}

# ETL defect: set to non-empty to simulate missing records (e.g. {"DRACD", "EASTC"})
DROPPED: set = set()

LOAD_TS = "2024-06-01 08:00:00"


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _ascii(s: str) -> str:
    """Normalize unicode → ASCII for safe identifiers/emails."""
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def _account_id(cid: str) -> str:
    return f"NW-{cid}"


def _contact_id(n: int) -> str:
    return f"CON-NW-{n:03}"


def _split_name(full: str):
    parts = _ascii(full).strip().split(" ", 1)
    return (parts[0], parts[1]) if len(parts) == 2 else (parts[0], "")


def _email(contact_name: str, company_name: str) -> str:
    first, last = _split_name(contact_name)
    domain = _ascii(company_name).lower()
    for ch in (" ", "'", "-", ".", ",", "&"):
        domain = domain.replace(ch, "")
    return f"{first[0].lower()}.{last.lower()}@{domain[:14]}.com"


def _created(i: int) -> str:
    return (date(2023, 1, 1) + timedelta(days=i * 16)).isoformat()


def _write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


# ─── Generator ────────────────────────────────────────────────────────────────
def generate() -> None:
    base = Path(__file__).parent.parent / "data"

    src_accounts, src_contacts = [], []

    for i, (cid, company, contact, title, city, region, country, phone) in enumerate(NORTHWIND_CUSTOMERS, 1):
        acc_type             = ACCOUNT_TYPE.get(title, "Partner")
        industry_name, _     = INDUSTRY.get(country, ("Distribution", "DIST"))
        revenue              = REVENUE_BASE.get(acc_type, 2_000_000) + (i * 75_000)
        lead_src             = LEAD_SOURCES[i % len(LEAD_SOURCES)]
        first, last          = _split_name(contact)
        cdate                = _created(i)

        src_accounts.append({
            "account_id":    _account_id(cid),
            "account_name":  company,
            "account_type":  acc_type,
            "industry":      industry_name,
            "annual_revenue": f"{revenue:.2f}",
            "phone":         phone,
            "billing_city":  city,
            "billing_state": region,
            "billing_country": country,
            "created_date":  cdate,
            "owner_id":      f"OWN-{300 + i}",
            "status":        "Active",
        })

        src_contacts.append({
            "contact_id":    _contact_id(i),
            "first_name":    first,
            "last_name":     last,
            "email":         _email(contact, company),
            "phone":         phone,
            "account_id":    _account_id(cid),
            "title":         title,
            "department":    ("Sales" if "Sales" in title
                              else "Management" if "Manager" in title
                              else "Operations"),
            "lead_source":   lead_src,
            "created_date":  cdate,
            "last_modified": "2024-05-20",
            "status":        "Active",
        })

    _write(base / "source" / "salesforce_accounts.csv", src_accounts)
    _write(base / "source" / "salesforce_contacts.csv", src_contacts)
    print(f"✓ Source  — {len(src_accounts)} accounts, {len(src_contacts)} contacts")

    # ── Target accounts: drop DROPPED to inject DEF-ETL-001 ─────────────────
    tgt_accounts = []
    for r in src_accounts:
        cid = r["account_id"].replace("NW-", "")
        if cid in DROPPED:
            continue
        _, ind_code = INDUSTRY.get(r["billing_country"], ("Distribution", "DIST"))
        tgt_accounts.append({
            "account_id":        r["account_id"],
            "client_name":       r["account_name"],
            "account_type":      r["account_type"],
            "industry_code":     ind_code,
            "annual_revenue_usd": r["annual_revenue"],
            "phone_number":      r["phone"],
            "city":              r["billing_city"],
            "state_code":        r["billing_state"],
            "country_code":      r["billing_country"],
            "created_date":      r["created_date"],
            "owner_id":          r["owner_id"],
            "record_status":     r["status"],
            "load_timestamp":    LOAD_TS,
        })

    # ── Target contacts: keep all rows → orphaned FK for dropped accounts ────
    tgt_contacts = []
    for r in src_contacts:
        first = r["first_name"]
        last  = r["last_name"]
        tgt_contacts.append({
            "contact_id":       r["contact_id"],
            "full_name":        f"{first} {last}",
            "email_address":    r["email"],
            "phone_number":     r["phone"],
            "account_id":       r["account_id"],
            "job_title":        r["title"],
            "department_name":  r["department"],
            "lead_source_code": LS_CODE.get(r["lead_source"], "OTHER"),
            "created_date":     r["created_date"],
            "last_updated":     r["last_modified"],
            "contact_status":   r["status"],
            "load_timestamp":   LOAD_TS,
        })

    _write(base / "target" / "warehouse_accounts.csv", tgt_accounts)
    _write(base / "target" / "warehouse_contacts.csv", tgt_contacts)

    dropped_contacts = [c["contact_id"] for c in tgt_contacts
                        if c["account_id"].replace("NW-", "") in DROPPED]

    print(f"✓ Target  — {len(tgt_accounts)} accounts "
          f"({len(DROPPED)} dropped: {sorted(DROPPED)}), "
          f"{len(tgt_contacts)} contacts")
    print(f"  Defects — DEF-ETL-001: missing accounts {sorted(DROPPED)}")
    print(f"            DEF-ETL-003/005: orphaned contacts {dropped_contacts}")


if __name__ == "__main__":
    generate()
