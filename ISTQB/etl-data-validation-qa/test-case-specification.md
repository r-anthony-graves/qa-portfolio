# Test Case Specification — ETL Data Validation Suite

| | |
|---|---|
| **Identifier** | TCS-ETL-001 |
| **Test basis** | Source/target CSVs under `data/`, TP-ETL-001 |
| **Automation** | `tests/test_etl_validation.py` (pytest + pandas, 22 test cases) |

Precondition for all test cases: the four CSV files load into pandas DataFrames
(fixtures `source_accounts`, `source_contacts`, `target_accounts`, `target_contacts`).

## 1. Test Cases

| TC ID | Test function | Req | Expected Result | Priority |
|---|---|---|---|---|
| TC-ETL-001 | `test_accounts_row_count_matches_source` | REQ-ETL-01 | Target account row count = source (20) | Critical |
| TC-ETL-001b | `test_contacts_row_count_matches_source` | REQ-ETL-01 | Target contact row count = source (20) | Critical |
| TC-ETL-001c | `test_all_source_account_ids_present_in_target` | REQ-ETL-01 | Every source `account_id` exists in target | Critical |
| TC-ETL-001d | `test_all_source_contact_ids_present_in_target` | REQ-ETL-01 | Every source `contact_id` exists in target | Critical |
| TC-ETL-002 | `test_account_name_maps_to_client_name` | REQ-ETL-02 | `account_name` → `client_name` values equal | High |
| TC-ETL-002b | `test_annual_revenue_preserved` | REQ-ETL-02 | `annual_revenue` → `annual_revenue_usd` exact match | High |
| TC-ETL-002c | `test_contact_name_concatenation` | REQ-ETL-02 | `first_name + last_name` → `full_name` | High |
| TC-ETL-002d | `test_phone_field_preserved` | REQ-ETL-02 | `phone` → `phone_number` preserved | Medium |
| TC-ETL-003 | `test_target_accounts_no_null_account_ids` | REQ-ETL-03 | No null `account_id` | Critical |
| TC-ETL-003b | `test_target_accounts_no_null_client_names` | REQ-ETL-03 | No null `client_name` | High |
| TC-ETL-003c | `test_target_contacts_no_null_emails` | REQ-ETL-03 | No null `email_address` | High |
| TC-ETL-003d | `test_target_contacts_no_null_account_fk` | REQ-ETL-03 | No null `account_id` FK | Critical |
| TC-ETL-003e | `test_target_accounts_revenue_non_negative` | REQ-ETL-03 | `annual_revenue_usd` ≥ 0 | Medium |
| TC-ETL-004 | `test_target_accounts_no_duplicate_ids` | REQ-ETL-04 | `account_id` unique | Critical |
| TC-ETL-004b | `test_target_contacts_no_duplicate_ids` | REQ-ETL-04 | `contact_id` unique | Critical |
| TC-ETL-004c | `test_target_contacts_no_duplicate_emails` | REQ-ETL-04 | Emails unique across contacts | Medium |
| TC-ETL-005 | `test_contact_account_fk_exists_in_accounts` | REQ-ETL-05 | Target contact FKs resolve to target accounts | Critical |
| TC-ETL-005b | `test_source_account_fks_consistent` | REQ-ETL-05 | Source contact FKs resolve to source accounts | High |
| TC-ETL-006 | `test_status_values_are_valid` | REQ-ETL-06 | `record_status` within allowed set | Medium |
| TC-ETL-006b | `test_contact_status_values_are_valid` | REQ-ETL-06 | `contact_status` within allowed set | Medium |
| TC-ETL-006c | `test_load_timestamp_present_for_all_target_records` | REQ-ETL-06 | Every target record has `load_timestamp` | Medium |
| TC-ETL-006d | `test_created_date_not_in_future` | REQ-ETL-06 | No `created_date` after run date | Low |

## 2. Requirements Traceability Matrix

| Req ID | Requirement | Test Cases | Coverage |
|---|---|---|---|
| REQ-ETL-01 | Record count reconciliation | TC-ETL-001 … 001d | ✅ 4 TCs |
| REQ-ETL-02 | Field mapping | TC-ETL-002 … 002d | ✅ 4 TCs |
| REQ-ETL-03 | Null validation | TC-ETL-003 … 003e | ✅ 5 TCs |
| REQ-ETL-04 | Duplicate detection | TC-ETL-004 … 004c | ✅ 3 TCs |
| REQ-ETL-05 | Referential integrity | TC-ETL-005, 005b | ✅ 2 TCs |
| REQ-ETL-06 | Business rules | TC-ETL-006 … 006d | ✅ 4 TCs |

All 6 requirements covered; 22 test cases total; no orphan test cases.

## 3. Negative-Path Verification

Setting `DROPPED={"DRACD","EASTC"}` in `scripts/generate_northwind_data.py` and
regenerating causes TC-ETL-001/001c (and dependent FK checks) to fail — confirming the
suite detects dropped records. Restore with `DROPPED=set()`.
