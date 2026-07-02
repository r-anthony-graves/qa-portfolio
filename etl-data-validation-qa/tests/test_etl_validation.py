"""
ETL Data Validation Test Suite — Salesforce to Data Warehouse
Project: etl-data-validation-qa
Tests validate record counts, field mappings, data types, null checks,
duplicate detection, business rules, and status field integrity.
"""

import pytest
import pandas as pd
from pathlib import Path


DATA = Path(__file__).parent.parent / "data"

SOURCE_ACCOUNTS  = DATA / "source" / "salesforce_accounts.csv"
SOURCE_CONTACTS  = DATA / "source" / "salesforce_contacts.csv"
TARGET_ACCOUNTS  = DATA / "target" / "warehouse_accounts.csv"
TARGET_CONTACTS  = DATA / "target" / "warehouse_contacts.csv"


@pytest.fixture(scope="session")
def source_accounts():
    return pd.read_csv(SOURCE_ACCOUNTS)

@pytest.fixture(scope="session")
def target_accounts():
    return pd.read_csv(TARGET_ACCOUNTS)

@pytest.fixture(scope="session")
def source_contacts():
    return pd.read_csv(SOURCE_CONTACTS)

@pytest.fixture(scope="session")
def target_contacts():
    return pd.read_csv(TARGET_CONTACTS)


# ─────────────────────────────────────────────────────────────────────────────
# TC-ETL-001  Record Count Reconciliation
# ─────────────────────────────────────────────────────────────────────────────
class TestRecordCountReconciliation:

    def test_accounts_row_count_matches_source(self, source_accounts, target_accounts):
        """TC-ETL-001 — REQ-ETL-01: Target account row count must equal source."""
        src_count = len(source_accounts)
        tgt_count = len(target_accounts)
        assert src_count == tgt_count, (
            f"Account count mismatch — Source: {src_count}, Target: {tgt_count}\n"
            f"Defect: DEF-ETL-001 | Missing records: {src_count - tgt_count}"
        )

    def test_contacts_row_count_matches_source(self, source_contacts, target_contacts):
        """TC-ETL-001b — REQ-ETL-01: Target contact row count must equal source."""
        src_count = len(source_contacts)
        tgt_count = len(target_contacts)
        assert src_count == tgt_count, (
            f"Contact count mismatch — Source: {src_count}, Target: {tgt_count}\n"
            f"Defect: DEF-ETL-002 | Missing records: {src_count - tgt_count}"
        )

    def test_all_source_account_ids_present_in_target(self, source_accounts, target_accounts):
        """TC-ETL-001c — Every source account_id must exist in target."""
        src_ids = set(source_accounts["account_id"])
        tgt_ids = set(target_accounts["account_id"])
        missing = src_ids - tgt_ids
        assert not missing, (
            f"Account IDs missing from target: {sorted(missing)}\n"
            f"Defect: DEF-ETL-003"
        )

    def test_all_source_contact_ids_present_in_target(self, source_contacts, target_contacts):
        """TC-ETL-001d — Every source contact_id must exist in target."""
        src_ids = set(source_contacts["contact_id"])
        tgt_ids = set(target_contacts["contact_id"])
        missing = src_ids - tgt_ids
        assert not missing, (
            f"Contact IDs missing from target: {sorted(missing)}\n"
            f"Defect: DEF-ETL-004"
        )


# ─────────────────────────────────────────────────────────────────────────────
# TC-ETL-002  Field Mapping Validation
# ─────────────────────────────────────────────────────────────────────────────
class TestFieldMapping:

    def test_account_name_maps_to_client_name(self, source_accounts, target_accounts):
        """TC-ETL-002 — REQ-ETL-02: account_name → client_name values must match."""
        src = source_accounts.set_index("account_id")["account_name"]
        tgt = target_accounts.set_index("account_id")["client_name"]
        common = src.index.intersection(tgt.index)
        mismatches = []
        for acc_id in common:
            if src[acc_id] != tgt[acc_id]:
                mismatches.append(f"{acc_id}: '{src[acc_id]}' → '{tgt[acc_id]}'")
        assert not mismatches, (
            f"Account name mapping failures (source → target):\n"
            + "\n".join(mismatches)
        )

    def test_annual_revenue_preserved(self, source_accounts, target_accounts):
        """TC-ETL-002b — REQ-ETL-02: annual_revenue → annual_revenue_usd must match exactly."""
        src = source_accounts.set_index("account_id")["annual_revenue"]
        tgt = target_accounts.set_index("account_id")["annual_revenue_usd"]
        common = src.index.intersection(tgt.index)
        mismatches = []
        for acc_id in common:
            if round(float(src[acc_id]), 2) != round(float(tgt[acc_id]), 2):
                mismatches.append(f"{acc_id}: source={src[acc_id]}, target={tgt[acc_id]}")
        assert not mismatches, (
            f"Annual revenue mapping mismatches:\n" + "\n".join(mismatches)
        )

    def test_contact_name_concatenation(self, source_contacts, target_contacts):
        """TC-ETL-002c — REQ-ETL-02: first_name + last_name → full_name transformation."""
        src = source_contacts.set_index("contact_id")[["first_name", "last_name"]]
        tgt = target_contacts.set_index("contact_id")["full_name"]
        common = src.index.intersection(tgt.index)
        mismatches = []
        for cid in common:
            expected = f"{src.loc[cid, 'first_name']} {src.loc[cid, 'last_name']}"
            actual = tgt[cid]
            if expected != actual:
                mismatches.append(f"{cid}: expected='{expected}', actual='{actual}'")
        assert not mismatches, (
            f"Contact name concatenation failures:\n" + "\n".join(mismatches)
        )

    def test_phone_field_preserved(self, source_contacts, target_contacts):
        """TC-ETL-002d — REQ-ETL-02: phone → phone_number must be preserved."""
        src = source_contacts.set_index("contact_id")["phone"]
        tgt = target_contacts.set_index("contact_id")["phone_number"]
        common = src.index.intersection(tgt.index)
        mismatches = [cid for cid in common if str(src[cid]) != str(tgt[cid])]
        assert not mismatches, (
            f"Phone number mapping failures for contacts: {mismatches}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# TC-ETL-003  Null / Empty Field Validation
# ─────────────────────────────────────────────────────────────────────────────
class TestNullValidation:

    def test_target_accounts_no_null_account_ids(self, target_accounts):
        """TC-ETL-003 — REQ-ETL-03: account_id must never be null in target."""
        nulls = target_accounts["account_id"].isnull().sum()
        assert nulls == 0, f"{nulls} null account_id values found in target accounts."

    def test_target_accounts_no_null_client_names(self, target_accounts):
        """TC-ETL-003b — REQ-ETL-03: client_name must never be null in target."""
        nulls = target_accounts["client_name"].isnull().sum()
        assert nulls == 0, f"{nulls} null client_name values in target accounts."

    def test_target_contacts_no_null_emails(self, target_contacts):
        """TC-ETL-003c — REQ-ETL-03: email_address must never be null in target contacts."""
        nulls = target_contacts["email_address"].isnull().sum()
        assert nulls == 0, f"{nulls} null email_address values in target contacts."

    def test_target_contacts_no_null_account_fk(self, target_contacts):
        """TC-ETL-003d — REQ-ETL-03: account_id FK must never be null in target contacts."""
        nulls = target_contacts["account_id"].isnull().sum()
        assert nulls == 0, f"{nulls} null account_id (FK) values in target contacts."

    def test_target_accounts_revenue_non_negative(self, target_accounts):
        """TC-ETL-003e — REQ-ETL-03: annual_revenue_usd must be >= 0."""
        negatives = target_accounts[target_accounts["annual_revenue_usd"] < 0]
        assert len(negatives) == 0, (
            f"Negative revenue values found:\n{negatives[['account_id','annual_revenue_usd']]}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# TC-ETL-004  Duplicate Detection
# ─────────────────────────────────────────────────────────────────────────────
class TestDuplicateDetection:

    def test_target_accounts_no_duplicate_ids(self, target_accounts):
        """TC-ETL-004 — REQ-ETL-04: No duplicate account_id allowed in target."""
        dupes = target_accounts[target_accounts["account_id"].duplicated(keep=False)]
        assert len(dupes) == 0, (
            f"Duplicate account IDs in target:\n{dupes[['account_id','client_name']]}"
        )

    def test_target_contacts_no_duplicate_ids(self, target_contacts):
        """TC-ETL-004b — REQ-ETL-04: No duplicate contact_id allowed in target."""
        dupes = target_contacts[target_contacts["contact_id"].duplicated(keep=False)]
        assert len(dupes) == 0, (
            f"Duplicate contact IDs in target:\n{dupes[['contact_id','full_name']]}"
        )

    def test_target_contacts_no_duplicate_emails(self, target_contacts):
        """TC-ETL-004c — REQ-ETL-04: Email addresses must be unique across contacts."""
        dupes = target_contacts[target_contacts["email_address"].duplicated(keep=False)]
        assert len(dupes) == 0, (
            f"Duplicate email addresses in target contacts:\n{dupes[['contact_id','email_address']]}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# TC-ETL-005  Referential Integrity
# ─────────────────────────────────────────────────────────────────────────────
class TestReferentialIntegrity:

    def test_contact_account_fk_exists_in_accounts(self, target_contacts, target_accounts):
        """TC-ETL-005 — REQ-ETL-05: Every contact account_id must exist in accounts table."""
        valid_account_ids = set(target_accounts["account_id"])
        orphaned = target_contacts[~target_contacts["account_id"].isin(valid_account_ids)]
        assert len(orphaned) == 0, (
            f"Orphaned contacts (FK not in accounts):\n"
            f"{orphaned[['contact_id', 'full_name', 'account_id']]}"
        )

    def test_source_account_fks_consistent(self, source_contacts, source_accounts):
        """TC-ETL-005b — REQ-ETL-05: Source contacts must reference valid source accounts."""
        valid_ids = set(source_accounts["account_id"])
        orphaned = source_contacts[~source_contacts["account_id"].isin(valid_ids)]
        assert len(orphaned) == 0, (
            f"Source data integrity issue — orphaned contacts:\n"
            f"{orphaned[['contact_id', 'first_name', 'account_id']]}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# TC-ETL-006  Business Rule Validation
# ─────────────────────────────────────────────────────────────────────────────
class TestBusinessRules:

    def test_status_values_are_valid(self, target_accounts):
        """TC-ETL-006 — REQ-ETL-06: record_status must be in allowed value set."""
        allowed = {"Active", "Inactive", "Pending"}
        invalid = target_accounts[~target_accounts["record_status"].isin(allowed)]
        assert len(invalid) == 0, (
            f"Invalid status values found:\n{invalid[['account_id','record_status']]}"
        )

    def test_contact_status_values_are_valid(self, target_contacts):
        """TC-ETL-006b — REQ-ETL-06: contact_status must be in allowed value set."""
        allowed = {"Active", "Inactive", "Pending"}
        invalid = target_contacts[~target_contacts["contact_status"].isin(allowed)]
        assert len(invalid) == 0, (
            f"Invalid contact status values:\n{invalid[['contact_id','contact_status']]}"
        )

    def test_load_timestamp_present_for_all_target_records(self, target_accounts):
        """TC-ETL-006c — REQ-ETL-06: Every target record must have a load_timestamp."""
        missing = target_accounts["load_timestamp"].isnull().sum()
        assert missing == 0, f"{missing} target accounts missing load_timestamp."

    def test_created_date_not_in_future(self, target_accounts):
        """TC-ETL-006d — REQ-ETL-06: created_date must not be a future date."""
        from datetime import date
        target_accounts["created_date_parsed"] = pd.to_datetime(target_accounts["created_date"])
        future = target_accounts[target_accounts["created_date_parsed"] > pd.Timestamp.today()]
        assert len(future) == 0, (
            f"Future created_date values found:\n{future[['account_id','created_date']]}"
        )
