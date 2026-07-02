# Test Plan — REST API Contract Testing Suite

| | |
|---|---|
| **Identifier** | TP-API-001 |
| **Suite** | `rest-api-contract-qa` |
| **Author** | R. Anthony Graves |
| **Date** | 2026-07-01 |
| **Status** | Approved |

## 1. Introduction & Objectives

Validate REST API behavioral and structural contracts over real HTTP in two tiers:
**offline** — the self-hosted Booking API: CRUD lifecycle, JSON Schema (Draft 2020-12)
compliance on every documented response, negative-path input handling, bearer-token
authentication, RFC 9110 idempotency semantics, and positive detection of three seeded
contract defects; **live** — the same patterns against the public Restful-Booker API
with real shared data, including documentation of its three known real-world contract
defects.

## 2. Test Items

- `api/booking_api.py` — self-hosted Flask Booking API: `/health`, `POST /auth/token`,
  bookings CRUD (GET/POST/PUT/DELETE), seeded with 3 bookings (BK-0001…BK-0003), and a
  `/legacy` blueprint carrying **3 seeded defects**:

  | ID | Seeded defect |
  |---|---|
  | DEF-API-01 | `GET /legacy/bookings/BK-9001` — schema drift (missing `status`, string `total_price`) |
  | DEF-API-02 | `POST /legacy/auth/login` — 401 message leaks account email + hash detail |
  | DEF-API-03 | `GET /legacy/bookings/{unknown}` — soft 404 (HTTP 200 + error body) |

- `schemas/` — 7 JSON Schemas: `booking`, `booking_list` (`$ref`s booking), `token`,
  `error`, `health`, plus `live_booking` and `live_create_response` for the live tier.
- **Live tier:** https://restful-booker.herokuapp.com — public API built for QA
  practice (documented demo credentials, shared mutable store, periodic reset) with
  **3 known real-world contract defects**:

  | ID | Real-world defect |
  |---|---|
  | LIVE-DEF-01 | `GET /ping` answers 201 Created for a read-only health probe |
  | LIVE-DEF-02 | `POST /auth` with bad credentials answers 200 + reason body, not 401 |
  | LIVE-DEF-03 | `DELETE /booking/{id}` answers 201 Created instead of 204/200 |

- `tests/test_rest_api_contract.py` — 26 offline test cases;
  `tests/test_live_restful_booker.py` — 11 live test cases (37 total).

## 3. Features to be Tested

| Req ID | Requirement |
|---|---|
| REQ-API-01 | CRUD lifecycle: 201+Location, roundtrip fidelity, immutable identity, 204→404 |
| REQ-API-02 | Every documented response validates against its JSON Schema, errors included |
| REQ-API-03 | Invalid input → 400 naming the field; unknown → 404; unsupported method → 405 |
| REQ-API-04 | Bearer-token auth: issuance, missing/tampered rejection, generic 401 hygiene |
| REQ-API-05 | PUT idempotent, DELETE not replayable, POST mints distinct resources |
| REQ-API-06 | All three seeded `/legacy` defects positively detected |
| REQ-API-07 | Live-tier interoperability: CRUD on live data, schema compliance, auth enforcement, and all three real-world defects documented |

## 4. Features Not to be Tested

- Performance/load characteristics, rate limiting, TLS certificate validation beyond
  library defaults, token expiry timing, pagination/filtering (not offered by either
  API), concurrency/race behavior, persistence across restarts (both stores are
  intentionally ephemeral), and other live users' data (the suite asserts only on
  bookings it creates itself).

## 5. Approach

- **Test level:** integration testing of the API contract at the HTTP boundary — the
  offline server runs in-process (`werkzeug.make_server` on a random free loopback
  port) but every request travels the full HTTP stack via `requests`, exactly as an
  external consumer would call it; the live tier calls Restful-Booker across the real
  internet.
- **Design techniques:** equivalence partitioning and boundary analysis on payload
  validation (missing/wrong-type/rule-violating input), state-transition testing on the
  resource lifecycle (created → updated → deleted → gone), specification-based testing
  against the JSON Schemas as the machine-readable contract, and **defect-based
  testing** — the three seeded `/legacy` defects and the three real-world LIVE-DEF
  defects must each be positively detected/reproduced.
- **Automation:** pytest with fixtures `base_url` (session-scoped local server), `http`
  (pooled session with enforced timeouts), `auth_headers` (real token via
  `/auth/token`), `validator_for` (Draft 2020-12 validators with cross-schema `$ref`
  resolution), an autouse store re-seed before every offline test for full isolation;
  live tier adds `live_api` (reachability gate → skip), `live_token`, and
  `live_booking` (self-created, best-effort deleted) with `pytest-rerunfailures`
  absorbing transient network flakiness (2 reruns, 2 s delay).

## 6. Item Pass/Fail Criteria

Suite passes at 37/37 (26 offline + 11 live), including positive detection of all
three seeded defects, reproduction of all three real-world live defects, and schema
validation of every documented response shape. With no network, 26/26 offline plus
11 SKIPPED is also a pass.

## 7. Entry / Exit Criteria

- **Entry:** all 7 schemas parse as valid Draft 2020-12; the local API server accepts
  connections; `/auth/token` issues a token for the demo credentials. Live tier
  additionally requires `GET /ping` on Restful-Booker to respond (otherwise: skip).
- **Exit:** all test cases executed or explicitly skipped; HTML report generated;
  every seeded and documented defect accounted for.

## 8. Test Environment

Windows 11 Pro, Python 3.14 (64-bit), pytest, Flask/Werkzeug dev server bound to
127.0.0.1 on a random free port. Offline tier needs no network; live tier reaches
https://restful-booker.herokuapp.com over HTTPS (base URL overridable via
`LIVE_API_BASE_URL`).

## 9. Risks & Contingencies

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Port collision with other local services | Low | Medium | Server binds port 0 (OS-assigned free port) |
| Cross-test state leakage via shared in-memory store | Medium | High | Autouse fixture re-seeds the store before every offline test |
| Hung request stalls the whole suite | Low | Medium | Timeouts on every HTTP call (5 s offline, 30 s live) |
| Seeded defects accidentally "fixed" during refactors | Medium | High | Defects are code-commented `DEF-API-*` and TCs assert their exact shape |
| Schema drift between `schemas/` and the implementation | Medium | High | That is the point of the suite — TC-API-002* fail on any divergence |
| Live service down / unreachable | Medium | Low | Reachability gate skips the live tier; offline tier unaffected |
| Live service flaky (cold starts, shared load) | Medium | Medium | 30 s timeouts + 2 automatic reruns per live test |
| Other users mutate the shared live store mid-run | Medium | Medium | Tests assert only on bookings they create; the list check asserts membership, not content |
| Upstream fixes a documented LIVE-DEF | Low | Low | Detecting tests fail loudly with a "fixed upstream?" message prompting a doc update |
