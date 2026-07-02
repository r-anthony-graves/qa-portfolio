# Test Case Specification — Workday Financial Validation Suite

| | |
|---|---|
| **Identifier** | TCS-WD-001 |
| **Test basis** | `workday_payroll_export.csv`, `hr_roster.csv`, `gl_entries.csv`, TP-WD-001 |
| **Automation** | `tests/test_payroll_validation.py` (pytest + pandas, 16 test cases) |

Precondition for all test cases: the three CSVs load into DataFrames; partitions
`active_payroll` / `terminated_payroll` derive from HR status.

## 1. Test Cases

| TC ID | Test function | Req | Expected Result | Priority |
|---|---|---|---|---|
| TC-WD-001 | `test_net_pay_equals_gross_minus_all_deductions` | REQ-WD-01 | net = gross − Σ(taxes + deductions), per employee | Critical |
| TC-WD-001b | `test_net_pay_always_positive` | REQ-WD-01 | Net pay > 0 for all active employees | High |
| TC-WD-001c | `test_gross_pay_greater_than_net_pay` | REQ-WD-01 | gross > net for all active employees | High |
| TC-WD-002 | `test_ss_tax_within_expected_range` | REQ-WD-02 | SS tax ≈ 6.2 % of gross (tolerance band) | Critical |
| TC-WD-002b | `test_medicare_tax_within_expected_range` | REQ-WD-02 | Medicare ≈ 1.45 % of gross (tolerance band) | Critical |
| TC-WD-002c | `test_no_negative_tax_values` | REQ-WD-02 | All tax amounts ≥ 0 | Medium |
| TC-WD-003 | `test_active_headcount_matches_between_hr_and_payroll` | REQ-WD-03 | Active HR count = active payroll count (14) | Critical |
| TC-WD-003b | `test_all_payroll_employees_exist_in_hr_roster` | REQ-WD-03 | Every payroll `employee_id` exists in HR | Critical |
| TC-WD-003c | `test_no_hr_active_employees_missing_from_payroll` | REQ-WD-03 | All active HR employees have payroll records | High |
| TC-WD-004 | `test_terminated_employees_flagged_in_payroll` | REQ-WD-04 | Terminated-in-payroll set matches HR termination list | High |
| TC-WD-004b | `test_known_terminated_employee_EMP010_flagged` | REQ-WD-04 | **EMP-010 (Angela Foster) flagged** | Critical |
| TC-WD-004c | `test_terminated_employees_should_trigger_review_flag` | REQ-WD-04 | Terminated employees paid in period → manual review | High |
| TC-WD-005 | `test_total_gross_pay_matches_gl_wage_entries` | REQ-WD-05 | Σ gross pay = GL wage debits | Critical |
| TC-WD-005b | `test_federal_tax_liability_posted_to_gl` | REQ-WD-05 | GL federal tax payable = payroll federal tax total | High |
| TC-WD-005c | `test_gl_entries_balance_debits_equal_credits` | REQ-WD-05 | Σ debits = Σ credits ($119,520 = $119,520) | Critical |
| TC-WD-005d | `test_every_employee_has_a_gl_entry` | REQ-WD-05 | Each employee has a GL gross-pay entry | Medium |

## 2. Requirements Traceability Matrix

| Req ID | Requirement | Test Cases | Coverage |
|---|---|---|---|
| REQ-WD-01 | Gross-to-net reconciliation | TC-WD-001 … 001c | ✅ 3 TCs |
| REQ-WD-02 | Tax calculation accuracy | TC-WD-002 … 002c | ✅ 3 TCs |
| REQ-WD-03 | Headcount reconciliation | TC-WD-003 … 003c | ✅ 3 TCs |
| REQ-WD-04 | Terminated employee validation | TC-WD-004 … 004c | ✅ 3 TCs |
| REQ-WD-05 | GL reconciliation | TC-WD-005 … 005d | ✅ 4 TCs |

All 5 requirements covered; 16 test cases total; no orphan test cases.

## 3. Known-Condition Probe

EMP-010 (Angela Foster) is terminated in `hr_roster.csv` but present in the payroll
export. TC-WD-004/004b/004c must flag her for manual review — proving the
cross-system control works, analogous to the seeded defects in the other suites.
