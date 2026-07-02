# Test Plan — ETL Data Validation Suite

| | |
|---|---|
| **Identifier** | TP-ETL-001 |
| **Suite** | `etl-data-validation-qa` |
| **Author** | R. Anthony Graves |
| **Date** | 2026-07-01 |
| **Status** | Approved |

## 1. Introduction & Objectives

Validate a simulated Salesforce → data-warehouse migration (Northwind-derived dataset,
20 accounts + 20 contacts) for completeness, correctness of field mapping, data quality,
and referential integrity. Demonstrates a standard ETL/data-migration validation approach.

## 2. Test Items

- Source extracts: `data/source/salesforce_accounts.csv`, `data/source/salesforce_contacts.csv`
- Target loads: `data/target/warehouse_accounts.csv`, `data/target/warehouse_contacts.csv`
- `tests/test_etl_validation.py` — 22 automated test cases (pytest + pandas)
- Support tooling: `scripts/generate_northwind_data.py` (regeneration + defect injection via
  `DROPPED={"DRACD","EASTC"}`), `scripts/verify_northwind_data.py` (27-point pre-check)

## 3. Features to be Tested

| Req ID | Requirement |
|---|---|
| REQ-ETL-01 | Record count reconciliation — target row counts and IDs match source |
| REQ-ETL-02 | Field mapping — renamed/transformed columns preserve values (`account_name→client_name`, `first+last→full_name`, etc.) |
| REQ-ETL-03 | Null validation — mandatory target columns contain no nulls; revenue ≥ 0 |
| REQ-ETL-04 | Duplicate detection — primary keys and emails unique in target |
| REQ-ETL-05 | Referential integrity — contact→account FKs resolve in both source and target |
| REQ-ETL-06 | Business rules — status enumerations, load timestamps, no future dates |

## 4. Features Not to be Tested

- ETL job orchestration/scheduling (data is validated post-load, batch-style).
- Performance/volume testing (dataset is intentionally small and deterministic).
- Incremental/CDC loads — full-load reconciliation only.

## 5. Approach

- **Test level:** integration (source-to-target data reconciliation).
- **Design techniques:** decision-table style column mapping checks, equivalence
  partitioning on status values, boundary checks (revenue ≥ 0, dates ≤ today), and
  **error seeding**: the generator script can drop accounts `DRACD`/`EASTC` to prove
  the count/ID checks fail when records go missing.
- **Automation:** pytest + pandas; source and target CSVs loaded via fixtures.

## 6. Item Pass/Fail Criteria

A test case passes when the pandas assertion holds across all rows. Suite passes at 22/22.

## 7. Entry / Exit Criteria

- **Entry:** all four CSVs present; `verify_northwind_data.py` reports 27/27 checks OK.
- **Exit:** all test cases executed; HTML report generated; any mismatch traced to
  extract, transform, or load stage.

## 8. Test Environment

Windows 11 Pro, Python 3.14 (64-bit), pytest, pandas. Fully offline.

## 9. Risks & Contingencies

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Static CSVs mask timing/latency issues of a real pipeline | High | Low | Scope limited to post-load validation by design |
| Regenerating data without re-running verify script | Low | Medium | 27-point verify script is an entry criterion |
| Float comparison noise on revenue values | Low | Low | Exact-match values chosen in the dataset |
