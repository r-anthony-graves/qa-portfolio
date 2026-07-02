# Test Summary Report — ETL Data Validation Suite

| | |
|---|---|
| **Identifier** | TSR-ETL-001 |
| **Reporting period** | Last execution as of 2026-07-01 |
| **References** | TP-ETL-001, TCS-ETL-001, `artifacts/report.html` |

## 1. Summary

All 22 test cases executed via pytest; **22 passed, 0 failed, 0 skipped**. Source-to-target
reconciliation of 20 accounts and 20 contacts confirmed complete and correct.

## 2. Results

| Test condition (class) | TCs | Passed | Failed |
|---|---|---|---|
| Record Count Reconciliation | 4 | 4 | 0 |
| Field Mapping | 4 | 4 | 0 |
| Null Validation | 5 | 5 | 0 |
| Duplicate Detection | 3 | 3 | 0 |
| Referential Integrity | 2 | 2 | 0 |
| Business Rules | 4 | 4 | 0 |
| **Total** | **22** | **22** | **0** |

## 3. Defects

No defects open. Data entry criteria confirmed beforehand by
`scripts/verify_northwind_data.py` (27/27 checks passed). Negative-path capability
(dropped-record injection via the generator script) verified during suite development.

## 4. Evaluation Against Exit Criteria

- All planned test cases executed — **met**.
- 100 % pass rate — **met**.
- HTML report generated — **met**.

## 5. Variances & Residual Risk

None for this cycle. Incremental/CDC load scenarios remain out of scope (TP-ETL-001 §4).

**Verdict: PASS — migration dataset validated end-to-end.**
