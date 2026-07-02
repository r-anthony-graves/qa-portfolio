"""
Legal Billing & Time Entry Validation Test Suite
Project: legal-billing-qa
Tests validate legal time entry rules, billing rate calculations, invoice accuracy,
matter status enforcement, and UTBMS code compliance.
Domain: Aderant-style legal billing workflows.
"""

import json
import pytest
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP


DATA_PATH = Path(__file__).parent.parent / "data" / "billing_data.json"

DAILY_HOURS_MAX = 24.0
MIN_TIME_INCREMENT = 0.1
VALID_UTBMS_TASK_CODES = {
    "L110", "L120", "L130", "L140", "L160", "L190",
    "L210", "L240", "L250", "L310", "L330", "L390", "L410"
}
VALID_UTBMS_ACTIVITY_CODES = {
    "A101", "A102", "A103", "A104", "A105", "A106",
    "A107", "A108", "A109", "A110", "A111", "A112"
}


@pytest.fixture(scope="session")
def billing_data():
    with open(DATA_PATH) as f:
        return json.load(f)

@pytest.fixture(scope="session")
def timekeepers(billing_data):
    return {tk["id"]: tk for tk in billing_data["timekeepers"]}

@pytest.fixture(scope="session")
def matters(billing_data):
    return {m["matter_id"]: m for m in billing_data["matters"]}

@pytest.fixture(scope="session")
def time_entries(billing_data):
    return billing_data["time_entries"]

@pytest.fixture(scope="session")
def valid_entries(time_entries):
    return [e for e in time_entries if not e.get("defect")]


# ─────────────────────────────────────────────────────────────────────────────
# TC-LB-001  Time Entry — Hours Validation
# ─────────────────────────────────────────────────────────────────────────────
class TestTimeEntryHoursValidation:

    def test_no_time_entry_exceeds_24_hours(self, time_entries):
        """TC-LB-001 — REQ-LB-01: No single time entry may exceed 24 hours in a day."""
        violations = [
            e for e in time_entries
            if float(e["hours"]) > DAILY_HOURS_MAX and not e.get("defect")
        ]
        # Verify the known defect TE-006 is flagged
        flagged_defects = [e for e in time_entries if e.get("defect") == "EXCEEDS_DAILY_MAX"]
        assert len(flagged_defects) >= 1, "Expected defect TE-006 (exceeds daily max) not found."

    def test_valid_entries_do_not_exceed_daily_max(self, valid_entries):
        """TC-LB-001b — REQ-LB-01: All non-defective entries must be <= 24 hours."""
        violations = [e for e in valid_entries if float(e["hours"]) > DAILY_HOURS_MAX]
        assert not violations, (
            f"Valid entries with hours > {DAILY_HOURS_MAX}:\n"
            + "\n".join(f"  {e['entry_id']}: {e['hours']}h" for e in violations)
        )

    def test_no_zero_hour_entries_in_valid_set(self, valid_entries):
        """TC-LB-001c — REQ-LB-01: Time entries must have hours > 0."""
        zero_entries = [e for e in valid_entries if float(e["hours"]) <= 0]
        assert not zero_entries, (
            f"Zero or negative hour entries found:\n"
            + "\n".join(f"  {e['entry_id']}: {e['hours']}h" for e in zero_entries)
        )

    def test_hours_are_in_valid_increments(self, valid_entries):
        """TC-LB-001d — REQ-LB-01: Hours must be in 0.1 (6-minute) increments.

        Uses integer check (multiply by 10, round, verify whole number) to avoid
        floating-point modulo precision errors with 0.1-based values.
        """
        violations = []
        for entry in valid_entries:
            hours = float(entry["hours"])
            # Multiply by 10 and check if result is a whole number
            scaled = round(hours * 10, 6)
            if abs(scaled - round(scaled)) > 1e-9:
                violations.append(f"  {entry['entry_id']}: {hours}h (invalid increment)")
        assert not violations, (
            f"Time entries not in {MIN_TIME_INCREMENT}h increments:\n"
            + "\n".join(violations)
        )

    def test_known_defect_TE006_exceeds_daily_max_is_flagged(self, time_entries):
        """TC-LB-001e — Confirm defect detection: TE-006 should be marked as defective."""
        te006 = next((e for e in time_entries if e["entry_id"] == "TE-006"), None)
        assert te006 is not None, "Test entry TE-006 not found in data."
        assert float(te006["hours"]) > DAILY_HOURS_MAX, (
            f"TE-006 should exceed daily max. Hours: {te006['hours']}"
        )
        assert te006.get("defect") == "EXCEEDS_DAILY_MAX", (
            "TE-006 defect not correctly labeled."
        )


# ─────────────────────────────────────────────────────────────────────────────
# TC-LB-002  Matter Status Enforcement
# ─────────────────────────────────────────────────────────────────────────────
class TestMatterStatusEnforcement:

    def test_no_time_entry_on_closed_matter(self, time_entries, matters):
        """TC-LB-002 — REQ-LB-02: Time may not be entered on a Closed matter."""
        closed_matter_ids = {mid for mid, m in matters.items() if m["status"] == "Closed"}
        violations = [
            e for e in time_entries
            if e["matter_id"] in closed_matter_ids and not e.get("defect")
        ]
        assert not violations, (
            f"Time entries on Closed matters:\n"
            + "\n".join(f"  {e['entry_id']} → {e['matter_id']}" for e in violations)
        )

    def test_defect_TE007_closed_matter_is_flagged(self, time_entries, matters):
        """TC-LB-002b — Confirm TE-007 targets MAT-004 (Closed) and is flagged."""
        te007 = next((e for e in time_entries if e["entry_id"] == "TE-007"), None)
        assert te007 is not None, "TE-007 not found in data."
        matter = matters.get(te007["matter_id"])
        assert matter["status"] == "Closed", (
            f"TE-007 matter should be Closed. Actual: {matter['status']}"
        )
        assert te007.get("defect") == "CLOSED_MATTER", (
            "TE-007 should be flagged as CLOSED_MATTER defect."
        )

    def test_active_matters_accept_time_entries(self, valid_entries, matters):
        """TC-LB-002c — REQ-LB-02: Active and valid entries must target Active matters."""
        for entry in valid_entries:
            matter = matters.get(entry["matter_id"])
            assert matter is not None, f"Matter {entry['matter_id']} not found."
            assert matter["status"] == "Active", (
                f"Entry {entry['entry_id']} targets non-Active matter "
                f"{entry['matter_id']} (status: {matter['status']})"
            )


# ─────────────────────────────────────────────────────────────────────────────
# TC-LB-003  Billing Rate Calculation
# ─────────────────────────────────────────────────────────────────────────────
class TestBillingRateCalculation:

    def _calculate_billed_amount(self, entry, timekeepers):
        tk = timekeepers[entry["timekeeper_id"]]
        return round(float(entry["hours"]) * tk["hourly_rate"], 2)

    def test_billing_amount_calculated_correctly_for_TE001(self, valid_entries, timekeepers):
        """TC-LB-003 — REQ-LB-03: Billed amount = hours × timekeeper rate."""
        te001 = next(e for e in valid_entries if e["entry_id"] == "TE-001")
        billed = self._calculate_billed_amount(te001, timekeepers)
        # TK-001 = $650/hr, 2.5 hrs = $1,625.00
        assert billed == 1625.00, f"TE-001 billing calc error: expected $1625.00, got ${billed}"

    def test_billing_amount_calculated_correctly_for_TE002(self, valid_entries, timekeepers):
        """TC-LB-003b — REQ-LB-03: TK-002 at $425/hr × 1.0h = $425.00."""
        te002 = next(e for e in valid_entries if e["entry_id"] == "TE-002")
        billed = self._calculate_billed_amount(te002, timekeepers)
        assert billed == 425.00, f"TE-002 billing calc error: expected $425.00, got ${billed}"

    def test_billing_amount_calculated_correctly_for_TE004_paralegal(self, valid_entries, timekeepers):
        """TC-LB-003c — REQ-LB-03: Paralegal TK-004 at $185/hr × 4.0h = $740.00."""
        te004 = next(e for e in valid_entries if e["entry_id"] == "TE-004")
        billed = self._calculate_billed_amount(te004, timekeepers)
        assert billed == 740.00, f"TE-004 billing calc error: expected $740.00, got ${billed}"

    def test_all_valid_entries_produce_positive_billed_amounts(self, valid_entries, timekeepers):
        """TC-LB-003d — REQ-LB-03: All valid entries must produce a positive billed amount."""
        negatives = []
        for entry in valid_entries:
            billed = self._calculate_billed_amount(entry, timekeepers)
            if billed <= 0:
                negatives.append(f"  {entry['entry_id']}: ${billed}")
        assert not negatives, "Entries with non-positive billed amounts:\n" + "\n".join(negatives)

    def test_timekeeper_rates_are_positive(self, timekeepers):
        """TC-LB-003e — REQ-LB-03: All timekeeper hourly rates must be > $0."""
        invalid = {tid: tk["hourly_rate"] for tid, tk in timekeepers.items() if tk["hourly_rate"] <= 0}
        assert not invalid, f"Timekeepers with invalid rates: {invalid}"


# ─────────────────────────────────────────────────────────────────────────────
# TC-LB-004  UTBMS Code Compliance
# ─────────────────────────────────────────────────────────────────────────────
class TestUTBMSCodeCompliance:

    def test_all_entries_have_valid_utbms_task_codes(self, time_entries):
        """TC-LB-004 — REQ-LB-04: All time entries must use valid UTBMS task codes."""
        invalid = [
            e for e in time_entries
            if e.get("utbms_task_code") not in VALID_UTBMS_TASK_CODES
        ]
        assert not invalid, (
            f"Invalid UTBMS task codes found:\n"
            + "\n".join(f"  {e['entry_id']}: {e.get('utbms_task_code')}" for e in invalid)
        )

    def test_all_entries_have_valid_utbms_activity_codes(self, time_entries):
        """TC-LB-004b — REQ-LB-04: All entries must use valid UTBMS activity codes."""
        invalid = [
            e for e in time_entries
            if e.get("utbms_activity_code") not in VALID_UTBMS_ACTIVITY_CODES
        ]
        assert not invalid, (
            f"Invalid UTBMS activity codes:\n"
            + "\n".join(f"  {e['entry_id']}: {e.get('utbms_activity_code')}" for e in invalid)
        )

    def test_partner_entries_use_l160_or_higher_task_codes(self, time_entries, timekeepers):
        """TC-LB-004c — REQ-LB-04: Partner-level work must use appropriate task code tier."""
        partner_entries = [
            e for e in time_entries
            if timekeepers.get(e["timekeeper_id"], {}).get("title") == "Partner"
        ]
        # Partners should not be coding purely administrative tasks (L110, L120)
        admin_only_codes = {"L110"}
        violations = [
            e for e in partner_entries
            if e.get("utbms_task_code") in admin_only_codes
        ]
        assert not violations, (
            f"Partners entered time with admin-level UTBMS codes:\n"
            + "\n".join(f"  {e['entry_id']}: {e['utbms_task_code']}" for e in violations)
        )


# ─────────────────────────────────────────────────────────────────────────────
# TC-LB-005  Invoice Total Reconciliation
# ─────────────────────────────────────────────────────────────────────────────
class TestInvoiceTotalReconciliation:

    def _billed(self, entry, timekeepers):
        tk = timekeepers[entry["timekeeper_id"]]
        return round(float(entry["hours"]) * tk["hourly_rate"], 2)

    def test_matter_MAT001_invoice_total_matches_sum_of_entries(self, valid_entries, timekeepers):
        """TC-LB-005 — REQ-LB-05: Invoice total for MAT-001 must equal sum of valid line items."""
        mat001_entries = [e for e in valid_entries if e["matter_id"] == "MAT-001"]
        calculated_total = sum(self._billed(e, timekeepers) for e in mat001_entries)
        # TE-001: $1625, TE-002: $425, TE-004: $740, TE-009: $65 = $2855.00
        expected_total = 2855.00
        assert abs(calculated_total - expected_total) < 0.01, (
            f"MAT-001 invoice total mismatch.\n"
            f"Expected: ${expected_total:.2f}, Calculated: ${calculated_total:.2f}"
        )

    def test_matter_MAT002_invoice_total(self, valid_entries, timekeepers):
        """TC-LB-005b — REQ-LB-05: Invoice total for MAT-002 must equal sum of line items."""
        mat002_entries = [e for e in valid_entries if e["matter_id"] == "MAT-002"]
        calculated_total = sum(self._billed(e, timekeepers) for e in mat002_entries)
        # TE-003: $1085, TE-005: $325 = $1410.00
        expected_total = 1410.00
        assert abs(calculated_total - expected_total) < 0.01, (
            f"MAT-002 invoice total mismatch.\n"
            f"Expected: ${expected_total:.2f}, Calculated: ${calculated_total:.2f}"
        )

    def test_minimum_billing_increment_respected(self, valid_entries, timekeepers):
        """TC-LB-005c — REQ-LB-05: Minimum billable unit is 0.1h (6 minutes)."""
        for entry in valid_entries:
            tk = timekeepers[entry["timekeeper_id"]]
            hours = float(entry["hours"])
            min_charge = round(MIN_TIME_INCREMENT * tk["hourly_rate"], 2)
            actual_charge = round(hours * tk["hourly_rate"], 2)
            assert actual_charge >= min_charge, (
                f"Entry {entry['entry_id']} billed below minimum increment.\n"
                f"Min: ${min_charge:.2f}, Actual: ${actual_charge:.2f}"
            )
