# Test Summary Report — REST API Contract Testing Suite

| | |
|---|---|
| **Identifier** | TSR-API-001 |
| **Reporting period** | Last execution as of 2026-07-01 |
| **References** | TP-API-001, TCS-API-001, `artifacts/report.html` |

## 1. Summary

All 37 test cases executed via pytest — 26 offline against a live loopback instance of
the Booking API and 11 live against the public Restful-Booker API; **37 passed,
0 failed, 0 skipped** in 2.85 s (no reruns needed this cycle). CRUD lifecycle, JSON
Schema contract compliance, negative-path handling, bearer-token auth, and idempotency
semantics all validated on both tiers; all three seeded contract defects on the
offline `/legacy` surface were positively detected, and all three real-world contract
defects of the live service were reproduced and documented.

## 2. Results

| Test condition (class) | Tier | TCs | Passed | Failed |
|---|---|---|---|---|
| CRUD Roundtrips | offline | 5 | 5 | 0 |
| JSON Schema Contract Compliance | offline | 5 | 5 | 0 |
| Negative Testing — Invalid Input | offline | 5 | 5 | 0 |
| Authentication & Authorization | offline | 5 | 5 | 0 |
| HTTP Idempotency Semantics | offline | 3 | 3 | 0 |
| Seeded Defect Detection | offline | 3 | 3 | 0 |
| Live CRUD & Contract (Restful-Booker) | live | 8 | 8 | 0 |
| Real-World Defect Documentation | live | 3 | 3 | 0 |
| **Total** | | **37** | **37** | **0** |

## 3. Defects

No product defects open on the modern offline API surface. Defect-detection
effectiveness: seeded **3/3**, real-world **3/3**.

Seeded (offline `/legacy` surface):

| ID | Defect | Outcome |
|---|---|---|
| DEF-API-01 | Schema drift on legacy record BK-9001 | Detected — fails `booking.schema.json` validation |
| DEF-API-02 | Account email + hash detail in legacy 401 body | Detected — email regex and internal-detail probes both hit |
| DEF-API-03 | Soft 404 (HTTP 200 + error body) on legacy unknown id | Detected — contrasted against the modern endpoint's real 404 |

Real-world (live Restful-Booker — known upstream defects, documented not reported):

| ID | Defect | Outcome |
|---|---|---|
| LIVE-DEF-01 | `GET /ping` answers 201 Created for a health probe | Reproduced |
| LIVE-DEF-02 | Bad credentials answer 200 + `{"reason"}` instead of 401 | Reproduced — offline TC-API-004b demonstrates the correct behavior |
| LIVE-DEF-03 | `DELETE` answers 201 Created instead of 204 | Reproduced — offline TC-API-001e demonstrates the correct behavior |

## 4. Evaluation Against Exit Criteria

- All planned test cases executed (none skipped; live service reachable) — **met**.
- 3/3 seeded defects detected; 3/3 real-world defects reproduced — **met**.
- Every documented response shape validates against its published schema, live
  responses included — **met**.
- Full HTTP stack exercised on both tiers (live server offline, real internet live;
  no test-client shortcuts) — **met**.
- Live tests touched only bookings the suite created itself — **met**.

## 5. Variances & Residual Risk

None for this cycle. The live tier depends on Restful-Booker's availability; when the
service is unreachable the tier reports SKIPPED and the offline tier stands alone
(TP-API-001 §6). The three LIVE-DEF tests will fail loudly if the upstream service
ever fixes its documented defects, prompting a documentation update. Performance, rate
limiting, TLS, token expiry timing, and concurrency remain out of scope (TP-API-001 §4).

**Verdict: PASS — the API contract checks are effective, demonstrably falsifiable, and
proven against live production data the suite does not control.**
