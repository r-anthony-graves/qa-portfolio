# Testing Requirements Specification — Workday Financial Validation Suite

| | |
|---|---|
| **Identifier** | TRS-WD-001 |
| **Suite** | `workday-financial-validation-qa` |
| **Test basis** | `workday_payroll_export.csv` (15 employees), `hr_roster.csv` (14 active + EMP-010 terminated), `gl_entries.csv` (22 entries, balanced at $119,520); IRS 2024 statutory rates |
| **Date** | 2026-07-01 |

Verification method for all requirements: **Test** (pytest + pandas three-way
reconciliation across payroll, HR, and GL extracts). Traceability: see TCS-WD-001 §2.

---

## REQ-WD-01 — Gross-to-Net Reconciliation

**Statement.** For every employee, net pay *shall* equal gross pay minus the sum of all
taxes and deductions; net pay *shall* be positive and strictly less than gross pay for
all active employees.

**Rationale.** Gross-to-net is the fundamental payroll equation; any residual indicates
a missing or double-counted deduction component.

**Acceptance criteria**
- `net_pay = gross_pay − (federal_tax + ss_tax + medicare_tax + other deductions)` per
  employee, to the cent.
- `net_pay > 0` and `gross_pay > net_pay` for all 14 active employees (range includes
  the Managing Partner at $22,000/period).

**Priority:** Critical · **Risk if unmet:** employees paid incorrectly; statutory filings wrong.
**Verified by:** TC-WD-001, 001b, 001c.

## REQ-WD-02 — Statutory Tax Calculation Accuracy

**Statement.** Withheld taxes *shall* match IRS 2024 statutory rates within tolerance:
Social Security 6.2 % of gross, Medicare 1.45 % of gross, federal withholding at the
configured effective rate of 22.5 %; no tax amount *shall* be negative.

**Rationale.** Employer under-withholding creates IRS liability plus penalties;
percentage-band checks catch both rate misconfiguration and per-employee anomalies.

**Acceptance criteria**
- `ss_tax / gross_pay` ≈ 0.062 within the defined tolerance band, per active employee.
- `medicare_tax / gross_pay` ≈ 0.0145 within tolerance, per active employee.
- All tax columns ≥ 0 for every payroll row (including terminated).
- *Documented simplification:* federal withholding is modelled as an effective flat
  22.5 %, not IRS bracket tables (see TP-WD-001 §9).

**Priority:** Critical · **Risk if unmet:** statutory non-compliance and penalties.
**Verified by:** TC-WD-002, 002b, 002c.

## REQ-WD-03 — Headcount Reconciliation (Payroll ⇄ HR)

**Statement.** The set of employees being paid *shall* exactly match the HR
system-of-record: equal active headcounts, no payroll record without an HR record, and
no active HR employee missing from payroll.

**Rationale.** The two failure directions differ in kind: a payroll-only record is a
potential **ghost employee** (fraud indicator); an HR-only active employee is a missed
paycheck (compliance/employee-relations incident).

**Acceptance criteria**
- Active count in HR (14) = active count in payroll (14).
- Every payroll `employee_id` exists in `hr_roster.csv`.
- Every HR employee with status Active has a payroll row for the period.

**Priority:** Critical · **Risk if unmet:** ghost-employee fraud or missed wages.
**Verified by:** TC-WD-003, 003b, 003c.

## REQ-WD-04 — Terminated Employee Controls

**Statement.** Any terminated employee appearing in the payroll run *shall* be flagged
for manual review, and the flagged set *shall* exactly match HR's termination list.

**Rationale.** Post-termination payments are a leading source of payroll overpayment;
they can be legitimate (final pay, payout of accrued leave) — hence *review*, not
auto-rejection — but must never pass silently.

**Acceptance criteria**
- Set of terminated employees present in payroll = set terminated in HR (here: exactly
  {EMP-010, Angela Foster}).
- EMP-010 is individually asserted as flagged (known-condition probe).
- Every such employee carries a manual-review flag in the run output.

**Priority:** Critical (probe) / High · **Risk if unmet:** overpayment after separation; clawback burden.
**Verified by:** TC-WD-004, 004b, 004c.

## REQ-WD-05 — General Ledger Reconciliation

**Statement.** Payroll results *shall* post to the general ledger completely and in
balance: wage debits equal total gross pay, federal tax payable matches the withheld
total, total debits equal total credits, and every employee has a gross-pay GL entry.

**Rationale.** Payroll that doesn't tie to the GL fails audit regardless of whether the
payments themselves were right; the debit=credit identity is the accounting invariant.

**Acceptance criteria**
- Σ payroll `gross_pay` = Σ GL wage-expense debits, to the cent.
- GL federal-tax-payable credit = Σ payroll federal tax withheld.
- Σ all GL debits = Σ all GL credits (dataset invariant: $119,520.00 = $119,520.00).
- Each of the 15 employees maps to at least one GL gross-pay entry (22 entries total).

**Priority:** Critical · **Risk if unmet:** unauditable books; period close blocked.
**Verified by:** TC-WD-005, 005b, 005c, 005d.
