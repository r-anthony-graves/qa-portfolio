# Test Summary Report — Workday Financial Validation Suite

| | |
|---|---|
| **Identifier** | TSR-WD-001 |
| **Reporting period** | Last execution as of 2026-07-01 |
| **References** | TP-WD-001, TCS-WD-001, `artifacts/report.html` |

## 1. Summary

All 16 test cases executed via pytest; **16 passed, 0 failed, 0 skipped**. Three-way
reconciliation (payroll ⇄ HR ⇄ GL) held: gross-to-net math correct for all 15
employees, statutory tax rates within band, headcount matched (14 active), and the
general ledger balanced exactly at **$119,520 debits = $119,520 credits**.

## 2. Results

| Test condition (class) | TCs | Passed | Failed |
|---|---|---|---|
| Gross-to-Net Reconciliation | 3 | 3 | 0 |
| Tax Calculation Accuracy | 3 | 3 | 0 |
| Headcount Reconciliation | 3 | 3 | 0 |
| Terminated Employee Validation | 3 | 3 | 0 |
| GL Reconciliation | 4 | 4 | 0 |
| **Total** | **16** | **16** | **0** |

## 3. Defects

No product defects open. The known-condition probe — terminated employee **EMP-010
(Angela Foster)** present in the payroll export — was correctly flagged for manual
review by TC-WD-004b/004c (control effectiveness: 1/1).

## 4. Evaluation Against Exit Criteria

- All planned test cases executed — **met**.
- GL balanced to the cent — **met**.
- Terminated-employee control fired — **met**.

## 5. Variances & Residual Risk

Federal withholding is modelled as an effective flat 22.5 % rather than IRS bracket
tables (documented simplification, TP-WD-001 §9). State/local tax out of scope.

**Verdict: PASS — payroll, HR, and GL extracts are mutually consistent.**
