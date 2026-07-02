# Test Summary Report — OrangeHRM UI Automation Suite

| | |
|---|---|
| **Identifier** | TSR-OHR-001 |
| **Reporting period** | As of 2026-07-01 |
| **References** | TP-OHR-001, TCS-OHR-001, `artifacts/reports/orangehrm_report.html` |

## 1. Summary

This suite runs against a **live third-party demo site** and is executed separately from
the data-driven suites (it is excluded from the dashboard's last-run counters). The
authoritative record of the most recent execution is the pytest-html report at
`artifacts/reports/orangehrm_report.html` and the screenshot evidence under `artifacts/`.

To produce a fresh cycle:

```bash
cd orangehrm-qa-project && python -m pytest
```

## 2. Planned vs. Executed

| Test area | Planned TCs | Notes |
|---|---|---|
| Login (positive/negative/required fields) | 4 | TC-OHR-003 is parametrized (multiple credential pairs) |
| Dashboard | 1 | |
| Navigation & logout | 3 | |
| Requirement screenshots | 8 | Evidence capture per module |
| **Total** | **16** | |

Results per cycle should be transcribed here from the HTML report after each run.

## 3. Defects

Record any live-site failures here, distinguishing:
- **Product defects** — genuine UI misbehaviour (report upstream; the demo is vendor-managed).
- **Environment incidents** — site downtime, rate limiting (rerun via pytest-rerunfailures).
- **Automation defects** — selector drift after vendor UI updates (fix locators).

## 4. Evaluation Against Exit Criteria

Exit requires all 16 tests passing (reruns permitted for transient network errors) and
the screenshot archive populated for all seven modules/flows.

## 5. Residual Risk

The system under test is shared and updated by the vendor without notice; green results
attest to the deployed version at execution time only. Pin expectations to structural
assertions, not record contents (TP-OHR-001 §9).

**Status: execution on demand — see HTML report for the latest cycle's verdict.**
