# Testing Requirements Specification — REST API Contract Testing Suite

| | |
|---|---|
| **Identifier** | TRS-API-001 |
| **Suite** | `rest-api-contract-qa` |
| **Test basis** | `api/booking_api.py` — self-hosted Booking REST API (health, token auth, bookings CRUD) incl. a `/legacy` surface carrying 3 seeded defects (DEF-API-01/02/03); `schemas/*.schema.json` — 7 JSON Schemas (Draft 2020-12); the live public Restful-Booker API (https://restful-booker.herokuapp.com) incl. 3 documented real-world contract defects (LIVE-DEF-01/02/03) |
| **Date** | 2026-07-01 |

Verification method for all requirements: **Test** (pytest assertions over real HTTP —
offline against a session-scoped local server on a random loopback port, live against
Restful-Booker; `jsonschema` validates response bodies against the published schemas).
Traceability: see TCS-API-001 §2.

---

## REQ-API-01 — CRUD Resource Lifecycle

**Statement.** The bookings resource *shall* support create (POST → 201 + `Location` +
echoed representation), read (GET item and collection with accurate `count`), full
update (PUT reflected on subsequent reads, identity and `created_at` immutable), and
delete (DELETE → 204 empty body, resource subsequently 404).

**Rationale.** The CRUD lifecycle is the behavioral contract every API consumer builds
on; a representation that diverges between POST response and subsequent GET, or a
delete that leaves the resource retrievable, silently corrupts client-side state.

**Acceptance criteria**
- POST returns 201, `Location: /bookings/{id}`, and echoes every client-supplied field;
  `status` defaults to `pending`.
- GET by id returns exactly the representation POST created.
- The collection lists created bookings and `count` equals the array length.
- PUT changes are visible on subsequent GET; `booking_id`/`created_at` never change.
- DELETE returns 204 with an empty body; a follow-up GET returns 404.

**Priority:** Critical · **Risk if unmet:** every downstream consumer breaks.
**Verified by:** TC-API-001, 001b, 001c, 001d, 001e.

## REQ-API-02 — JSON Schema Contract Compliance

**Statement.** Every documented response body *shall* validate against its published
JSON Schema (Draft 2020-12): `/health`, the booking item and collection, the token
response, and all structured error bodies (`{"error": {"code", "message"}}`).

**Rationale.** Schema validation catches contract drift — a field silently renamed,
retyped, or dropped — that functional assertions on individual fields miss. The schema
files are the machine-readable API contract.

**Acceptance criteria**
- `GET /health`, `GET /bookings`, `GET /bookings/{id}`, and `POST /auth/token` (success)
  each validate against their schema; collection items validate via `$ref` to the
  booking schema.
- 404 and 405 responses validate against `error.schema.json` (JSON, never HTML).

**Priority:** Critical · **Risk if unmet:** undetected breaking changes ship to consumers.
**Verified by:** TC-API-002, 002b, 002c, 002d, 002e.

## REQ-API-03 — Negative-Path Input Handling

**Statement.** Invalid input *shall* be rejected with HTTP 400 and a structured error
naming the offending field: missing required fields, wrong types (no silent coercion of
`total_price` strings), syntactically malformed JSON, and business-rule violations
(`check_out` must be after `check_in`). Unknown resources *shall* return 404 and
unsupported methods 405.

**Rationale.** APIs that coerce bad input or answer it with 500 stack traces push
validation cost onto every consumer and leak implementation detail.

**Acceptance criteria**
- Omitting `guest_email` → 400, message names the field.
- `total_price` as a string → 400 (rejected, not coerced).
- Malformed JSON body → 400 `MALFORMED_JSON`, not 500.
- `check_out` ≤ `check_in` → 400, message names the rule.
- Unknown booking id → 404; PATCH on the item resource → 405.

**Priority:** High · **Risk if unmet:** garbage data persisted; internals leaked via 500s.
**Verified by:** TC-API-003, 003b, 003c, 003d, 003e.

## REQ-API-04 — Bearer-Token Authentication

**Statement.** Valid credentials *shall* yield a bearer token; all write methods (POST,
PUT, DELETE) *shall* require a valid token and reject missing or tampered tokens with
401. Failed logins *shall* return a generic message exposing neither account emails nor
which credential field was wrong.

**Rationale.** Tokens must be validated by value, not shape — a token with one flipped
character must fail. Verbose 401 messages enable account enumeration (contrast seeded
DEF-API-02, which does exactly that on the legacy surface).

**Acceptance criteria**
- Valid demo credentials → 200 with `{token, token_type: bearer, expires_in}`.
- Wrong credentials → 401; body contains no token, no email, no field hint.
- POST without a token → 401 `UNAUTHORIZED`.
- The valid token with its last character altered → 401.
- One valid token authorizes POST, PUT, and DELETE.

**Priority:** Critical · **Risk if unmet:** unauthorized writes; account enumeration.
**Verified by:** TC-API-004, 004b, 004c, 004d, 004e.

## REQ-API-05 — HTTP Idempotency Semantics

**Statement.** PUT *shall* be idempotent (identical replays produce identical
representations and status); DELETE *shall* succeed once and answer replays with 404;
POST *shall not* be idempotent (each request mints a distinct resource).

**Rationale.** Retry logic in clients, proxies, and message queues is built on RFC 9110
method semantics; a PUT that mutates differently on replay breaks safe retries.

**Acceptance criteria**
- Two identical PUTs → 200 both, byte-identical representations.
- DELETE → 204, immediate replay → 404.
- Two identical POSTs → two distinct `booking_id`s.

**Priority:** High · **Risk if unmet:** unsafe retries duplicate or corrupt state.
**Verified by:** TC-API-005, 005b, 005c.

## REQ-API-06 — Seeded Defect Detection (`/legacy` surface)

**Statement.** The suite *shall* positively detect the three defects seeded on the
legacy endpoints, proving each class of contract check is falsifiable.

**Seeded defects**

| ID | Endpoint | Defect |
|---|---|---|
| DEF-API-01 | `GET /legacy/bookings/BK-9001` | Schema drift: `status` missing, `total_price` serialized as a string |
| DEF-API-02 | `POST /legacy/auth/login` | 401 message leaks an account email and internal hash detail (PII in error body) |
| DEF-API-03 | `GET /legacy/bookings/{unknown}` | "Soft 404": HTTP 200 with an error body instead of 404 |

**Acceptance criteria**
- BK-9001 **must fail** validation against `booking.schema.json`.
- The legacy 401 message **must match** an email pattern and mention internal hash detail.
- The legacy unknown-id response **must be** HTTP 200 with `{"error": "booking not found"}`,
  while the modern endpoint answers the identical case with a real 404.

**Priority:** Critical · **Risk if unmet:** the contract checks themselves are untrustworthy.
**Verified by:** TC-API-006, 006b, 006c.

## REQ-API-07 — Live API Interoperability & Real-World Defect Documentation

**Statement.** The same contract-testing patterns *shall* execute against the live
public Restful-Booker API using real shared data: full CRUD on bookings the suite
creates itself (never other users' records), schema validation of live responses,
token-based write authorization, and positive documentation of the service's known
real-world contract defects. The live tier *shall* skip cleanly when the service is
unreachable and *shall* absorb transient network flakiness via automatic reruns.

**Rationale.** Deterministic offline checks prove the method; running the identical
patterns against a live service with data the suite does not control proves the method
survives reality — cold starts, shared mutable state, and an API whose defects are
real rather than seeded.

**Documented real-world defects (live counterparts to the seeded DEF-API set)**

| ID | Endpoint | Defect |
|---|---|---|
| LIVE-DEF-01 | `GET /ping` | Health probe answers 201 Created (read-only request claiming resource creation) |
| LIVE-DEF-02 | `POST /auth` (bad credentials) | HTTP 200 + `{"reason": "Bad credentials"}` instead of 401 |
| LIVE-DEF-03 | `DELETE /booking/{id}` | Answers 201 Created instead of 204/200 |

**Acceptance criteria**
- Create → read → update (PUT and PATCH) → delete roundtrips succeed on live data;
  responses validate against `live_booking` / `live_create_response` schemas.
- Writes without a token are refused (403) and leave the booking unchanged.
- An impossible booking id yields a real 404.
- Each LIVE-DEF **must** be reproduced exactly; the detecting tests fail the day the
  upstream service fixes the defect, forcing a documentation update.
- With no network, every live test case reports SKIPPED, not FAILED.

**Priority:** High · **Risk if unmet:** the method is only proven on data we control.
**Verified by:** TC-API-007 … 007h, TC-API-008 … 008c.
