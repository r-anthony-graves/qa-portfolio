# Test Summary Report — AI Prompt Validation Suite

| | |
|---|---|
| **Identifier** | TSR-AI-001 |
| **Reporting period** | Last execution as of 2026-07-01 |
| **References** | TP-AI-001, TCS-AI-001, `artifacts/report.html` |

## 1. Summary

All 18 test cases executed via pytest; **18 passed, 0 failed, 0 skipped**. The suite
verified factual accuracy, refusal behaviour, format compliance, hallucination
prevention, scope adherence, PII safety, bias balance, and latency budget across the
10-prompt catalog.

## 2. Results

| Test condition (class) | TCs | Passed | Failed |
|---|---|---|---|
| Factual Accuracy | 2 | 2 | 0 |
| Refusal Behavior | 3 | 3 | 0 |
| Format Compliance | 4 | 4 | 0 |
| Hallucination Detection | 2 | 2 | 0 |
| PII Safety | 3 | 3 | 0 |
| Bias Detection | 2 | 2 | 0 |
| Response Performance | 2 | 2 | 0 |
| **Total** | **18** | **18** | **0** |

## 3. Defects

No product defects open. The one **seeded** defect (PII echoed in a PC-006 response
variant) was correctly detected by TC-AI-005b — this is the expected outcome and proves
the PII check can fail when it should (error-seeding effectiveness: 1/1).

## 4. Evaluation Against Exit Criteria

- All planned test cases executed — **met**.
- 100 % pass rate including seeded-defect detection — **met**.
- HTML report generated — **met**.

## 5. Variances & Residual Risk

- Latency assertions run against recorded metadata, not live calls; live-model drift is
  not covered by this cycle (see TP-AI-001 §9).
- Duplicated `TC-AI-007` IDs were renumbered to `TC-AI-008/008b` on 2026-07-01
  (TP-AI-001 §10) — no retest needed, docstring-only change.

**Verdict: PASS — suite fit for regression use.**
