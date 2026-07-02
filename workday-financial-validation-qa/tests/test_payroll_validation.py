"""
Workday Financial Data Validation Test Suite
Project: workday-financial-validation-qa
Tests validate payroll reconciliation, gross-to-net accuracy, GL code mapping,
headcount matching, terminated employee flags, and deduction totals.
"""

import pytest
import pandas as pd
from pathlib import Path


DATA = Path(__file__).parent.parent / "data"

PAYROLL_PATH = DATA / "workday_payroll_export.csv"
GL_PATH      = DATA / "gl_entries.csv"
ROSTER_PATH  = DATA / "hr_roster.csv"

FEDERAL_TAX_RATE = 0.225   # 22.5% effective rate
SS_TAX_RATE      = 0.062   # 6.2%
MEDICARE_RATE    = 0.0145  # 1.45%


@pytest.fixture(scope="session")
def payroll():
    df = pd.read_csv(PAYROLL_PATH)
    df["gross_pay"]              = pd.to_numeric(df["gross_pay"],              errors="coerce")
    df["federal_tax"]            = pd.to_numeric(df["federal_tax"],            errors="coerce")
    df["state_tax"]              = pd.to_numeric(df["state_tax"],              errors="coerce")
    df["ss_tax"]                 = pd.to_numeric(df["ss_tax"],                 errors="coerce")
    df["medicare_tax"]           = pd.to_numeric(df["medicare_tax"],           errors="coerce")
    df["health_ins_deduction"]   = pd.to_numeric(df["health_ins_deduction"],   errors="coerce")
    df["retirement_401k"]        = pd.to_numeric(df["retirement_401k"],        errors="coerce")
    df["net_pay"]                = pd.to_numeric(df["net_pay"],                errors="coerce")
    return df

@pytest.fixture(scope="session")
def gl_entries():
    return pd.read_csv(GL_PATH)

@pytest.fixture(scope="session")
def hr_roster():
    return pd.read_csv(ROSTER_PATH)

@pytest.fixture(scope="session")
def active_payroll(payroll):
    return payroll[payroll["status"] == "Active"]

@pytest.fixture(scope="session")
def terminated_payroll(payroll):
    return payroll[payroll["status"] == "Terminated"]


# ─────────────────────────────────────────────────────────────────────────────
# TC-WD-001  Gross-to-Net Pay Reconciliation
# ─────────────────────────────────────────────────────────────────────────────
class TestGrossToNetReconciliation:

    def test_net_pay_equals_gross_minus_all_deductions(self, payroll):
        """TC-WD-001 — REQ-WD-01: net_pay = gross_pay - all taxes and deductions."""
        mismatches = []
        for _, row in payroll.iterrows():
            calculated_net = round(
                row["gross_pay"]
                - row["federal_tax"]
                - row["state_tax"]
                - row["ss_tax"]
                - row["medicare_tax"]
                - row["health_ins_deduction"]
                - row["retirement_401k"],
                2
            )
            if abs(calculated_net - round(row["net_pay"], 2)) > 0.01:
                mismatches.append(
                    f"  {row['employee_id']} {row['last_name']}: "
                    f"expected net=${calculated_net:.2f}, recorded=${row['net_pay']:.2f}"
                )
        assert not mismatches, (
            f"Gross-to-net reconciliation failures:\n" + "\n".join(mismatches)
        )

    def test_net_pay_always_positive(self, active_payroll):
        """TC-WD-001b — REQ-WD-01: Net pay must be positive for all active employees."""
        negatives = active_payroll[active_payroll["net_pay"] <= 0]
        assert len(negatives) == 0, (
            f"Negative or zero net pay found:\n"
            f"{negatives[['employee_id', 'last_name', 'net_pay']]}"
        )

    def test_gross_pay_greater_than_net_pay(self, active_payroll):
        """TC-WD-001c — REQ-WD-01: gross_pay must always exceed net_pay."""
        violations = active_payroll[active_payroll["gross_pay"] <= active_payroll["net_pay"]]
        assert len(violations) == 0, (
            f"Records where net >= gross:\n"
            f"{violations[['employee_id', 'gross_pay', 'net_pay']]}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# TC-WD-002  Tax Calculation Accuracy
# ─────────────────────────────────────────────────────────────────────────────
class TestTaxCalculationAccuracy:

    def test_ss_tax_within_expected_range(self, active_payroll):
        """TC-WD-002 — REQ-WD-02: SS tax should be ~6.2% of gross pay."""
        tolerance = 0.005  # 0.5% tolerance
        violations = []
        for _, row in active_payroll.iterrows():
            expected_ss = round(row["gross_pay"] * SS_TAX_RATE, 2)
            actual_ss   = round(row["ss_tax"], 2)
            pct_diff = abs(actual_ss - expected_ss) / expected_ss if expected_ss else 0
            if pct_diff > tolerance:
                violations.append(
                    f"  {row['employee_id']}: expected SS=${expected_ss:.2f}, "
                    f"actual=${actual_ss:.2f} ({pct_diff:.1%} diff)"
                )
        assert not violations, "SS tax calculation deviations:\n" + "\n".join(violations)

    def test_medicare_tax_within_expected_range(self, active_payroll):
        """TC-WD-002b — REQ-WD-02: Medicare tax should be ~1.45% of gross pay."""
        tolerance = 0.005
        violations = []
        for _, row in active_payroll.iterrows():
            expected_med = round(row["gross_pay"] * MEDICARE_RATE, 2)
            actual_med   = round(row["medicare_tax"], 2)
            pct_diff = abs(actual_med - expected_med) / expected_med if expected_med else 0
            if pct_diff > tolerance:
                violations.append(
                    f"  {row['employee_id']}: expected Medicare=${expected_med:.2f}, "
                    f"actual=${actual_med:.2f}"
                )
        assert not violations, "Medicare tax deviations:\n" + "\n".join(violations)

    def test_no_negative_tax_values(self, payroll):
        """TC-WD-002c — REQ-WD-02: All tax amounts must be >= 0."""
        tax_cols = ["federal_tax", "state_tax", "ss_tax", "medicare_tax"]
        for col in tax_cols:
            negatives = payroll[payroll[col] < 0]
            assert len(negatives) == 0, (
                f"Negative {col} values found:\n"
                f"{negatives[['employee_id', col]]}"
            )


# ─────────────────────────────────────────────────────────────────────────────
# TC-WD-003  Headcount Reconciliation (HR Roster vs Payroll)
# ─────────────────────────────────────────────────────────────────────────────
class TestHeadcountReconciliation:

    def test_active_headcount_matches_between_hr_and_payroll(self, hr_roster, active_payroll):
        """TC-WD-003 — REQ-WD-03: Active headcount in HR must match active payroll count."""
        hr_active_count  = len(hr_roster[hr_roster["status"] == "Active"])
        pay_active_count = len(active_payroll)
        assert hr_active_count == pay_active_count, (
            f"Headcount mismatch — HR Active: {hr_active_count}, "
            f"Payroll Active: {pay_active_count}"
        )

    def test_all_payroll_employees_exist_in_hr_roster(self, payroll, hr_roster):
        """TC-WD-003b — REQ-WD-03: Every payroll employee_id must exist in HR roster."""
        roster_ids  = set(hr_roster["employee_id"])
        payroll_ids = set(payroll["employee_id"])
        missing = payroll_ids - roster_ids
        assert not missing, f"Payroll employees not in HR roster: {missing}"

    def test_no_hr_active_employees_missing_from_payroll(self, hr_roster, payroll):
        """TC-WD-003c — REQ-WD-03: Active HR employees must all have payroll records."""
        active_hr_ids  = set(hr_roster[hr_roster["status"] == "Active"]["employee_id"])
        payroll_ids    = set(payroll["employee_id"])
        missing_from_payroll = active_hr_ids - payroll_ids
        assert not missing_from_payroll, (
            f"Active HR employees with no payroll record: {missing_from_payroll}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# TC-WD-004  Terminated Employee Validation
# ─────────────────────────────────────────────────────────────────────────────
class TestTerminatedEmployeeValidation:

    def test_terminated_employees_flagged_in_payroll(self, terminated_payroll, hr_roster):
        """TC-WD-004 — REQ-WD-04: Terminated employees in payroll must match HR termination list."""
        hr_terminated_ids = set(
            hr_roster[hr_roster["status"] == "Terminated"]["employee_id"]
        )
        payroll_terminated_ids = set(terminated_payroll["employee_id"])
        # All payroll-terminated must exist in HR terminated list
        unexpected = payroll_terminated_ids - hr_terminated_ids
        assert not unexpected, (
            f"Payroll shows terminated status for employees not terminated in HR: {unexpected}"
        )

    def test_known_terminated_employee_EMP010_flagged(self, terminated_payroll):
        """TC-WD-004b — REQ-WD-04: EMP-010 (Angela Foster) is terminated and must be flagged."""
        emp010 = terminated_payroll[terminated_payroll["employee_id"] == "EMP-010"]
        assert len(emp010) == 1, (
            "EMP-010 (terminated) should appear once in payroll with Terminated status."
        )
        assert emp010.iloc[0]["status"] == "Terminated", (
            f"EMP-010 payroll status should be 'Terminated'. Found: {emp010.iloc[0]['status']}"
        )

    def test_terminated_employees_should_trigger_review_flag(self, terminated_payroll):
        """TC-WD-004c — REQ-WD-04: Terminated employees paid in period require manual review."""
        # Terminated employees may still receive final pay — but must be reviewed
        if len(terminated_payroll) > 0:
            for _, row in terminated_payroll.iterrows():
                assert row["net_pay"] >= 0, (
                    f"Terminated employee {row['employee_id']} has negative net pay "
                    f"— review required."
                )


# ─────────────────────────────────────────────────────────────────────────────
# TC-WD-005  GL Entry Reconciliation
# ─────────────────────────────────────────────────────────────────────────────
class TestGLReconciliation:

    def test_total_gross_pay_matches_gl_wage_entries(self, payroll, gl_entries):
        """TC-WD-005 — REQ-WD-05: Sum of gross_pay in payroll must equal GL wage debits."""
        payroll_total = round(payroll["gross_pay"].sum(), 2)
        gl_wage_accounts = {"5010", "5020"}
        gl_wages = gl_entries[
            gl_entries["account_code"].astype(str).isin(gl_wage_accounts)
        ]
        gl_total = round(gl_wages["debit_amount"].sum(), 2)
        assert abs(payroll_total - gl_total) < 0.01, (
            f"Gross pay reconciliation failure.\n"
            f"Payroll total: ${payroll_total:,.2f}\n"
            f"GL wage total: ${gl_total:,.2f}\n"
            f"Difference: ${abs(payroll_total - gl_total):.2f}"
        )

    def test_federal_tax_liability_posted_to_gl(self, payroll, gl_entries):
        """TC-WD-005b — REQ-WD-05: Federal tax payable in GL must match payroll total."""
        payroll_fed_total = round(payroll["federal_tax"].sum(), 2)
        gl_fed = gl_entries[gl_entries["account_code"] == 2010]
        gl_fed_total = round(gl_fed["credit_amount"].sum(), 2)
        assert abs(payroll_fed_total - gl_fed_total) < 0.01, (
            f"Federal tax GL mismatch.\n"
            f"Payroll: ${payroll_fed_total:,.2f} | GL: ${gl_fed_total:,.2f}"
        )

    def test_gl_entries_balance_debits_equal_credits(self, gl_entries):
        """TC-WD-005c — REQ-WD-05: Total GL debits must equal total GL credits for period."""
        total_debits  = round(gl_entries["debit_amount"].sum(), 2)
        total_credits = round(gl_entries["credit_amount"].sum(), 2)
        assert abs(total_debits - total_credits) < 0.01, (
            f"GL is out of balance!\n"
            f"Total Debits:  ${total_debits:,.2f}\n"
            f"Total Credits: ${total_credits:,.2f}\n"
            f"Difference:    ${abs(total_debits - total_credits):.2f}"
        )

    def test_every_employee_has_a_gl_entry(self, payroll, gl_entries):
        """TC-WD-005d — REQ-WD-05: Each employee must have a corresponding GL gross pay entry."""
        payroll_ids = set(payroll["employee_id"])
        gl_emp_ids  = set(gl_entries["employee_id"].dropna())
        missing = payroll_ids - gl_emp_ids
        assert not missing, (
            f"Employees with no GL entry: {sorted(missing)}"
        )
