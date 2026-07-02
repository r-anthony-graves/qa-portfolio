# Test Plan — Workday Financial Validation Suite

| | |
|---|---|
| **Identifier** | TP-WD-001 |
| **Suite** | `workday-financial-validation-qa` |
| **Author** | R. Anthony Graves |
| **Date** | 2026-07-01 |
| **Status** | Approved |

## 1. Introduction & Objectives

Validate a Workday-style payroll export against the HR roster and the general ledger:
gross-to-net arithmetic, statutory tax accuracy (real IRS 2024 rates — Social Security
6.2 %, Medicare 1.45 %, federal withholding 22.5 % effective), headcount reconciliation,
terminated-employee handling, and GL balancing.

## 2. Test Items

- `data/workday_payroll_export.csv` — 15 employees (incl. Managing Partner, $22k/period)
- `data/hr_roster.csv` — 15 employees (14 active; EMP-010 terminated)
- `data/gl_entries.csv` — 22 GL entries; total debits = credits = **$119,520** (balanced)
- `tests/test_payroll_validation.py` — 16 automated test cases (pytest + pandas)

## 3. Features to be Tested

| Req ID | Requirement |
|---|---|
| REQ-WD-01 | Gross-to-net: net = gross − (all taxes + deductions); net > 0; gross > net |
| REQ-WD-02 | Tax accuracy: SS ≈ 6.2 %, Medicare ≈ 1.45 % of gross; no negative tax values |
| REQ-WD-03 | Headcount: active HR count = active payroll count; all payroll IDs exist in HR; all active HR employees have payroll records |
| REQ-WD-04 | Terminated employees paid in period are flagged for manual review and match the HR termination list |
| REQ-WD-05 | GL reconciliation: gross pay = wage debits; federal tax payable matches; Σ debits = Σ credits; every employee has a GL gross-pay entry |

## 4. Features Not to be Tested

- State/local taxes, benefits enrollment logic, retro pay, multi-currency,
  Workday API integration (validation is file-based).

## 5. Approach

- **Test level:** integration testing across three systems-of-record extracts
  (payroll ⇄ HR ⇄ GL), i.e. three-way reconciliation.
- **Design techniques:** recomputation oracles (net pay, tax percentages within
  tolerance bands), cross-dataset set comparisons (headcount, ID membership), and a
  known-condition probe: **EMP-010 (Angela Foster)** is terminated in HR yet present in
  payroll and must be flagged for review.
- **Automation:** pytest + pandas fixtures `payroll`, `active_payroll`,
  `terminated_payroll`, `hr_roster`, `gl_entries`.

## 6. Item Pass/Fail Criteria

Suite passes at 16/16, including the EMP-010 terminated-employee flag and an exactly
balanced GL.

## 7. Entry / Exit Criteria

- **Entry:** all three CSVs present and parseable; GL verified balanced at data build time.
- **Exit:** all test cases executed; HTML report generated; discrepancies traced to
  payroll, HR, or GL side.

## 8. Test Environment

Windows 11 Pro, Python 3.14 (64-bit), pytest, pandas. Fully offline.

## 9. Risks & Contingencies

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Percentage tolerance bands hide small tax errors | Medium | Medium | Bands set tight around statutory rates |
| Flat 22.5 % federal proxy diverges from bracket math | High | Low | Documented simplification; suite guards consistency, not IRS tables |
| Currency rounding across 3 files | Medium | Medium | Cent-level tolerances on reconciliation sums |
