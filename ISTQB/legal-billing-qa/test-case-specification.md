# Test Case Specification — Legal Billing Validation Suite

| | |
|---|---|
| **Identifier** | TCS-LB-001 |
| **Test basis** | `data/billing_data.json` (7 timekeepers, 6 matters, 16 entries), TP-LB-001 |
| **Automation** | `tests/test_billing_validation.py` (pytest, 19 test cases) |

Precondition for all test cases: `billing_data.json` loads; fixture `valid_entries` is
the partition of entries without a `defect` field.

## 1. Test Cases

| TC ID | Test function | Req | Expected Result | Priority |
|---|---|---|---|---|
| TC-LB-001 | `test_no_time_entry_exceeds_24_hours` | REQ-LB-01 | Entries > 24 h are only the flagged defect (TE-006) | Critical |
| TC-LB-001b | `test_valid_entries_do_not_exceed_daily_max` | REQ-LB-01 | All valid entries ≤ 24 h | High |
| TC-LB-001c | `test_no_zero_hour_entries_in_valid_set` | REQ-LB-01 | Valid entries all have hours > 0 | High |
| TC-LB-001d | `test_hours_are_in_valid_increments` | REQ-LB-01 | Valid entries use 0.1 h increments | Medium |
| TC-LB-001e | `test_known_defect_TE006_exceeds_daily_max_is_flagged` | REQ-LB-01 | **Seeded TE-006 (25 h) is flagged** | Critical |
| TC-LB-002 | `test_no_time_entry_on_closed_matter` | REQ-LB-02 | No unflagged entry targets a Closed matter | Critical |
| TC-LB-002b | `test_defect_TE007_closed_matter_is_flagged` | REQ-LB-02 | **Seeded TE-007 (MAT-004 Closed) is flagged** | Critical |
| TC-LB-002c | `test_active_matters_accept_time_entries` | REQ-LB-02 | Valid entries target Active matters | Medium |
| TC-LB-003 | `test_billing_amount_calculated_correctly_for_TE001` | REQ-LB-03 | TE-001 amount = hours × rate | High |
| TC-LB-003b | `test_billing_amount_calculated_correctly_for_TE002` | REQ-LB-03 | TK-002 $425/hr × 1.0 h = $425.00 | High |
| TC-LB-003c | `test_billing_amount_calculated_correctly_for_TE004_paralegal` | REQ-LB-03 | TK-004 $185/hr × 4.0 h = $740.00 | High |
| TC-LB-003d | `test_all_valid_entries_produce_positive_billed_amounts` | REQ-LB-03 | Every valid entry bills > $0 | Medium |
| TC-LB-003e | `test_timekeeper_rates_are_positive` | REQ-LB-03 | All hourly rates > $0 | Medium |
| TC-LB-004 | `test_all_entries_have_valid_utbms_task_codes` | REQ-LB-04 | Task codes within UTBMS set | High |
| TC-LB-004b | `test_all_entries_have_valid_utbms_activity_codes` | REQ-LB-04 | Activity codes within UTBMS set | High |
| TC-LB-004c | `test_partner_entries_use_l160_or_higher_task_codes` | REQ-LB-04 | Partner work uses appropriate task-code tier | Medium |
| TC-LB-005 | `test_matter_MAT001_invoice_total_matches_sum_of_entries` | REQ-LB-05 | MAT-001 invoice = Σ valid line items | Critical |
| TC-LB-005b | `test_matter_MAT002_invoice_total` | REQ-LB-05 | MAT-002 invoice = Σ valid line items | Critical |
| TC-LB-005c | `test_minimum_billing_increment_respected` | REQ-LB-05 | Minimum billable unit 0.1 h enforced (TE-016 excluded) | High |

## 2. Requirements Traceability Matrix

| Req ID | Requirement | Test Cases | Coverage |
|---|---|---|---|
| REQ-LB-01 | Hours validation | TC-LB-001 … 001e | ✅ 5 TCs |
| REQ-LB-02 | Matter status enforcement | TC-LB-002 … 002c | ✅ 3 TCs |
| REQ-LB-03 | Rate calculation | TC-LB-003 … 003e | ✅ 5 TCs |
| REQ-LB-04 | UTBMS compliance | TC-LB-004 … 004c | ✅ 3 TCs |
| REQ-LB-05 | Invoice reconciliation | TC-LB-005 … 005c | ✅ 3 TCs |

All 5 requirements covered; 19 test cases total; no orphan test cases.

## 3. Seeded Defect Coverage

| Seeded defect | Entry | Detected by |
|---|---|---|
| EXCEEDS_DAILY_MAX | TE-006 | TC-LB-001, TC-LB-001e |
| CLOSED_MATTER | TE-007 | TC-LB-002, TC-LB-002b |
| ZERO_HOURS | TE-010 | TC-LB-001c (exclusion from valid set) |
| BELOW_MIN_INCREMENT | TE-016 | TC-LB-001d, TC-LB-005c |
