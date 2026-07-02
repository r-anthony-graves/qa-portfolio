# Test Plan — Legal Billing Validation Suite

| | |
|---|---|
| **Identifier** | TP-LB-001 |
| **Suite** | `legal-billing-qa` |
| **Author** | R. Anthony Graves |
| **Date** | 2026-07-01 |
| **Status** | Approved |

## 1. Introduction & Objectives

Validate law-firm time-entry and billing data against firm business rules: daily-hours
limits, matter status enforcement, rate calculation, UTBMS task/activity code compliance,
and invoice reconciliation. Rates reflect 2024 ABA billing benchmarks.

## 2. Test Items

- `data/billing_data.json` — 7 timekeepers (incl. TK-006 Counsel $550/hr, TK-007 Summer
  Associate $225/hr), 6 matters, 16 time entries of which **4 carry seeded defects**:

  | Entry | Seeded defect |
  |---|---|
  | TE-006 | `EXCEEDS_DAILY_MAX` (25.0 h in one day) |
  | TE-007 | `CLOSED_MATTER` (time on MAT-004, status Closed) |
  | TE-010 | `ZERO_HOURS` (0.0 h entry) |
  | TE-016 | `BELOW_MIN_INCREMENT` (0.05 h < 0.1 h minimum) |

- `tests/test_billing_validation.py` — 19 automated test cases.

## 3. Features to be Tested

| Req ID | Requirement |
|---|---|
| REQ-LB-01 | Time entry hours: 0 < hours ≤ 24, in 0.1 h increments |
| REQ-LB-02 | No time may be entered on a Closed matter |
| REQ-LB-03 | Billed amount = hours × timekeeper rate; all rates > $0 |
| REQ-LB-04 | All entries use valid UTBMS task and activity codes; partner work uses the appropriate task-code tier |
| REQ-LB-05 | Invoice totals equal the sum of valid line items; minimum billable unit 0.1 h (6 min) |

## 4. Features Not to be Tested

- E-billing submission formats (LEDES file generation), client-specific billing guidelines,
  write-offs/discounts, trust accounting.

## 5. Approach

- **Test level:** system testing of billing business rules on a deterministic dataset.
- **Design techniques:** boundary value analysis (24 h daily max, 0.1 h minimum
  increment, $0 rate), decision tables (matter status × entry acceptance), and
  **defect-based testing** — the four seeded defects must each be flagged, and the
  "valid entries" partition must exclude them from invoice math.
- **Automation:** pytest with fixtures `timekeepers`, `matters`, `time_entries`,
  `valid_entries` (defect-free partition).

## 6. Item Pass/Fail Criteria

Suite passes at 19/19, including positive detection of all four seeded defects and
invoice totals computed from the valid partition only.

## 7. Entry / Exit Criteria

- **Entry:** `billing_data.json` parses; all referenced timekeeper/matter IDs resolve.
- **Exit:** all test cases executed; HTML report generated; every seeded defect accounted for.

## 8. Test Environment

Windows 11 Pro, Python 3.14 (64-bit), pytest. Fully offline.

## 9. Risks & Contingencies

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Floating-point drift in currency math | Medium | Medium | Amounts asserted with cent-level tolerance |
| UTBMS code list incomplete vs. full ABA set | Low | Low | Codes limited to those used in the dataset |
| Seeded defects accidentally "fixed" during data edits | Medium | High | Defects carry explicit `defect` field; TCs assert their presence |
