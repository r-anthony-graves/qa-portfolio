"""Verify all Northwind-generated ETL data files."""
import pandas as pd
from pathlib import Path

DATA = Path(__file__).parent.parent / "data"

sa = pd.read_csv(DATA / "source/salesforce_accounts.csv")
sc = pd.read_csv(DATA / "source/salesforce_contacts.csv")
ta = pd.read_csv(DATA / "target/warehouse_accounts.csv")
tc = pd.read_csv(DATA / "target/warehouse_contacts.csv")

PASS = "  ✓"
FAIL = "  ✗"

def check(label, ok, detail=""):
    status = PASS if ok else FAIL
    print(f"{status}  {label}" + (f"  →  {detail}" if detail else ""))
    return ok

# ─── Counts ──────────────────────────────────────────────────────────────────
print("\n── RECORD COUNTS ──────────────────────────────────────────────────")
check("Source accounts  = 20", len(sa) == 20, f"{len(sa)} rows")
check("Source contacts  = 20", len(sc) == 20, f"{len(sc)} rows")
check("Target accounts  = 18 (2 intentionally dropped)", len(ta) == 18, f"{len(ta)} rows")
check("Target contacts  = 20 (all kept → orphaned FK defect)", len(tc) == 20, f"{len(tc)} rows")

missing_accs = sorted(set(sa.account_id) - set(ta.account_id))
check("Dropped accounts = NW-DRACD, NW-EASTC",
      missing_accs == ["NW-DRACD", "NW-EASTC"], str(missing_accs))

# ─── Nulls ───────────────────────────────────────────────────────────────────
print("\n── NULL CHECKS ─────────────────────────────────────────────────────")
check("Source accounts: no null account_id",   sa.account_id.isnull().sum() == 0)
check("Source accounts: no null account_name", sa.account_name.isnull().sum() == 0)
check("Source contacts: no null contact_id",   sc.contact_id.isnull().sum() == 0)
check("Source contacts: no null account_id FK",sc.account_id.isnull().sum() == 0)
check("Target accounts: no null account_id",   ta.account_id.isnull().sum() == 0)
check("Target accounts: no null client_name",  ta.client_name.isnull().sum() == 0)
check("Target contacts: no null email_address",tc.email_address.isnull().sum() == 0)
check("Target contacts: no null account_id FK",tc.account_id.isnull().sum() == 0)
check("Target accounts: load_timestamp present",ta.load_timestamp.isnull().sum() == 0)

# ─── Duplicates ──────────────────────────────────────────────────────────────
print("\n── DUPLICATE CHECKS ────────────────────────────────────────────────")
check("Source accounts: unique account_id",  sa.account_id.duplicated().sum() == 0)
check("Source contacts: unique contact_id",  sc.contact_id.duplicated().sum() == 0)
check("Target accounts: unique account_id",  ta.account_id.duplicated().sum() == 0)
check("Target contacts: unique contact_id",  tc.contact_id.duplicated().sum() == 0)
check("Target contacts: unique email_address",tc.email_address.duplicated().sum() == 0,
      f"{tc.email_address.duplicated().sum()} dupes")

# ─── Field mapping ───────────────────────────────────────────────────────────
print("\n── FIELD MAPPING CHECKS ────────────────────────────────────────────")
src_name = sa.set_index("account_id")["account_name"]
tgt_name = ta.set_index("account_id")["client_name"]
common   = src_name.index.intersection(tgt_name.index)
name_mm  = [i for i in common if src_name[i] != tgt_name[i]]
check("account_name → client_name: no mismatches", len(name_mm) == 0,
      f"{len(name_mm)} mismatches" if name_mm else f"{len(common)} records match")

src_rev = sa.set_index("account_id")["annual_revenue"].astype(float)
tgt_rev = ta.set_index("account_id")["annual_revenue_usd"].astype(float)
rev_mm  = [i for i in common if round(src_rev[i], 2) != round(tgt_rev[i], 2)]
check("annual_revenue → annual_revenue_usd: no mismatches", len(rev_mm) == 0,
      f"{len(common)} records match")

src_c    = sc.set_index("contact_id")[["first_name", "last_name"]]
tgt_full = tc.set_index("contact_id")["full_name"]
cc       = src_c.index.intersection(tgt_full.index)
full_mm  = [i for i in cc
            if (src_c.loc[i, "first_name"] + " " + src_c.loc[i, "last_name"]) != tgt_full[i]]
check("first_name + last_name → full_name: no mismatches", len(full_mm) == 0,
      f"{len(cc)} records match")

src_ph = sc.set_index("contact_id")["phone"]
tgt_ph = tc.set_index("contact_id")["phone_number"]
ph_mm  = [i for i in cc if str(src_ph[i]) != str(tgt_ph[i])]
check("phone → phone_number: no mismatches", len(ph_mm) == 0,
      f"{len(cc)} records match")

# ─── Business rules ───────────────────────────────────────────────────────────
print("\n── BUSINESS RULE CHECKS ────────────────────────────────────────────")
valid_status = {"Active", "Inactive", "Pending"}
bad_acc = ta[~ta.record_status.isin(valid_status)]
bad_con = tc[~tc.contact_status.isin(valid_status)]
check("Target accounts: all record_status valid",  len(bad_acc) == 0,
      f"invalid: {list(bad_acc.record_status.unique())}" if len(bad_acc) else "all Active")
check("Target contacts: all contact_status valid", len(bad_con) == 0,
      f"invalid: {list(bad_con.contact_status.unique())}" if len(bad_con) else "all Active")
neg_rev = ta[ta.annual_revenue_usd.astype(float) < 0]
check("Target accounts: no negative revenue",       len(neg_rev) == 0)

from datetime import date
ta["_cd"] = pd.to_datetime(ta["created_date"])
future = ta[ta["_cd"] > pd.Timestamp.today()]
check("Target accounts: no future created_date",   len(future) == 0,
      f"min={ta._cd.min().date()}  max={ta._cd.max().date()}")

# ─── Referential integrity ────────────────────────────────────────────────────
print("\n── REFERENTIAL INTEGRITY ───────────────────────────────────────────")
orphaned = tc[~tc.account_id.isin(ta.account_id)]
check("Source FK integrity: all source contacts → valid source accounts",
      sc[~sc.account_id.isin(sa.account_id)].empty)
check("Target FK defect present (DEF-ETL-005): 2 orphaned contacts",
      len(orphaned) == 2,
      f"orphaned: {list(zip(orphaned.contact_id, orphaned.account_id))}")

# ─── Summary ─────────────────────────────────────────────────────────────────
print("\n── NORTHWIND DATA OVERVIEW ─────────────────────────────────────────")
print(f"  Countries     : {sorted(sa.billing_country.unique())}")
print(f"  Account types : {dict(sa.account_type.value_counts())}")
print(f"  Industries    : {dict(sa.industry.value_counts())}")
print(f"  Revenue range : ${sa.annual_revenue.astype(float).min():,.0f}"
      f" – ${sa.annual_revenue.astype(float).max():,.0f}")
print(f"  Contact titles: {sorted(sc.title.unique())}")
print()
