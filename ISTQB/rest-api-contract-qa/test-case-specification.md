# Test Case Specification — REST API Contract Testing Suite

| | |
|---|---|
| **Identifier** | TCS-API-001 |
| **Test basis** | `api/booking_api.py` (Booking API + `/legacy` seeded defects), `schemas/*.schema.json` (7 schemas), the live Restful-Booker API, TP-API-001 |
| **Automation** | `tests/test_rest_api_contract.py` (26 offline TCs) + `tests/test_live_restful_booker.py` (11 live TCs) — pytest, 37 test cases |

Precondition for offline test cases (TC-API-001…006c): the local API server is live on
a random loopback port (`base_url` fixture); the booking store is re-seeded to
BK-0001…BK-0003 before every test; `auth_headers` carries a real token issued by
`POST /auth/token`. Precondition for live test cases (TC-API-007…008c):
Restful-Booker answers `GET /ping` (otherwise all live TCs are SKIPPED); `live_token`
holds a real token from `POST /auth`; `live_booking` is created by the test itself.

## 1. Test Cases

| TC ID | Test function | Req | Expected Result | Priority |
|---|---|---|---|---|
| TC-API-001 | `test_create_returns_201_location_and_echoed_body` | REQ-API-01 | 201, `Location` header, all fields echoed, status defaults `pending` | Critical |
| TC-API-001b | `test_get_by_id_returns_created_representation` | REQ-API-01 | GET returns exactly the POST representation | Critical |
| TC-API-001c | `test_list_includes_created_booking_and_accurate_count` | REQ-API-01 | Collection contains new booking; `count` = array length | High |
| TC-API-001d | `test_put_update_is_reflected_on_subsequent_get` | REQ-API-01 | Update visible on GET; `booking_id`/`created_at` immutable | Critical |
| TC-API-001e | `test_delete_returns_204_then_resource_is_gone` | REQ-API-01 | 204 empty body; follow-up GET → 404 | Critical |
| TC-API-002 | `test_health_endpoint_matches_health_schema` | REQ-API-02 | `/health` validates against `health.schema.json` | Medium |
| TC-API-002b | `test_booking_collection_matches_list_schema` | REQ-API-02 | Collection validates; items validate via `$ref` | Critical |
| TC-API-002c | `test_single_booking_matches_booking_schema` | REQ-API-02 | BK-0001 validates against `booking.schema.json` | Critical |
| TC-API-002d | `test_token_response_matches_token_schema` | REQ-API-02 | Token body validates against `token.schema.json` | High |
| TC-API-002e | `test_error_bodies_match_error_schema` | REQ-API-02 | 404 and 405 bodies validate against `error.schema.json` | High |
| TC-API-003 | `test_missing_required_field_rejected_with_400_naming_the_field` | REQ-API-03 | 400; message names `guest_email` | High |
| TC-API-003b | `test_wrong_type_total_price_rejected_with_400` | REQ-API-03 | String `total_price` rejected, not coerced | High |
| TC-API-003c | `test_malformed_json_body_rejected_with_400` | REQ-API-03 | 400 `MALFORMED_JSON`, not a 500 | High |
| TC-API-003d | `test_checkout_on_or_before_checkin_rejected_with_400` | REQ-API-03 | Business rule enforced; message names `check_out` | High |
| TC-API-003e | `test_unknown_resource_404_and_unsupported_method_405` | REQ-API-03 | Unknown id → 404; PATCH → 405 | Medium |
| TC-API-004 | `test_valid_credentials_issue_token` | REQ-API-04 | 200 with bearer token | Critical |
| TC-API-004b | `test_wrong_credentials_rejected_with_generic_401` | REQ-API-04 | 401; no token, no email, no field hint in message | Critical |
| TC-API-004c | `test_write_without_token_rejected_with_401` | REQ-API-04 | POST without token → 401 `UNAUTHORIZED` | Critical |
| TC-API-004d | `test_tampered_token_rejected_with_401` | REQ-API-04 | Token with last char flipped → 401 | Critical |
| TC-API-004e | `test_valid_token_authorizes_all_write_methods` | REQ-API-04 | One token authorizes POST, PUT, DELETE | High |
| TC-API-005 | `test_put_is_idempotent` | REQ-API-05 | Two identical PUTs → identical 200 representations | High |
| TC-API-005b | `test_delete_is_not_replayable` | REQ-API-05 | 204 then 404 on replay | High |
| TC-API-005c | `test_post_is_not_idempotent` | REQ-API-05 | Identical POSTs mint distinct `booking_id`s | Medium |
| TC-API-006 | `test_DEF_API_01_legacy_record_violates_booking_schema` | REQ-API-06 | **Seeded BK-9001 fails schema validation** | Critical |
| TC-API-006b | `test_DEF_API_02_legacy_login_error_leaks_pii` | REQ-API-06 | **Seeded email + hash leak detected in 401 body** | Critical |
| TC-API-006c | `test_DEF_API_03_legacy_unknown_id_returns_soft_404` | REQ-API-06 | **Seeded soft 404 (HTTP 200 + error body) detected; modern endpoint returns real 404** | Critical |
| TC-API-007 | `test_live_create_roundtrip_and_envelope_schema` | REQ-API-07 | Live POST echoes payload in a schema-valid `{bookingid, booking}` envelope | Critical |
| TC-API-007b | `test_live_get_by_id_matches_payload_and_schema` | REQ-API-07 | Live GET returns the stored booking, schema-valid | Critical |
| TC-API-007c | `test_live_collection_lists_created_booking` | REQ-API-07 | Live index contains the booking this test created | High |
| TC-API-007d | `test_live_put_full_update_with_token` | REQ-API-07 | Live PUT with token cookie replaces the booking; visible on GET | High |
| TC-API-007e | `test_live_patch_updates_only_the_target_field` | REQ-API-07 | Live PATCH changes only the submitted field | High |
| TC-API-007f | `test_live_write_without_token_is_rejected` | REQ-API-07 | Tokenless PUT/DELETE → 403; booking unchanged | Critical |
| TC-API-007g | `test_live_unknown_booking_id_returns_404` | REQ-API-07 | Impossible live id → real 404 | Medium |
| TC-API-007h | `test_live_auth_issues_token_for_documented_credentials` | REQ-API-07 | Live `/auth` issues a usable token | High |
| TC-API-008 | `test_LIVE_DEF_01_ping_returns_201_for_a_health_probe` | REQ-API-07 | **Real defect LIVE-DEF-01 reproduced: /ping → 201** | Medium |
| TC-API-008b | `test_LIVE_DEF_02_bad_credentials_return_200_not_401` | REQ-API-07 | **Real defect LIVE-DEF-02 reproduced: bad creds → 200 + reason** | High |
| TC-API-008c | `test_LIVE_DEF_03_delete_returns_201_instead_of_204` | REQ-API-07 | **Real defect LIVE-DEF-03 reproduced: DELETE → 201, then 404 on GET** | High |

## 2. Requirements Traceability Matrix

| Req ID | Requirement | Test Cases | Coverage |
|---|---|---|---|
| REQ-API-01 | CRUD resource lifecycle | TC-API-001 … 001e | ✅ 5 TCs |
| REQ-API-02 | JSON Schema contract compliance | TC-API-002 … 002e | ✅ 5 TCs |
| REQ-API-03 | Negative-path input handling | TC-API-003 … 003e | ✅ 5 TCs |
| REQ-API-04 | Bearer-token authentication | TC-API-004 … 004e | ✅ 5 TCs |
| REQ-API-05 | HTTP idempotency semantics | TC-API-005 … 005c | ✅ 3 TCs |
| REQ-API-06 | Seeded defect detection | TC-API-006 … 006c | ✅ 3 TCs |
| REQ-API-07 | Live interoperability & real-world defects | TC-API-007 … 008c | ✅ 11 TCs |

All 7 requirements covered; 37 test cases total; no orphan test cases.

## 3. Defect Coverage

Seeded (offline, `/legacy` surface):

| Seeded defect | Endpoint | Detected by |
|---|---|---|
| DEF-API-01 — schema drift | `GET /legacy/bookings/BK-9001` | TC-API-006 (`jsonschema.ValidationError` raised) |
| DEF-API-02 — PII in error body | `POST /legacy/auth/login` | TC-API-006b (email regex + hash detail); TC-API-004b proves the modern endpoint is clean |
| DEF-API-03 — soft 404 | `GET /legacy/bookings/{unknown}` | TC-API-006c; TC-API-003e proves the modern endpoint returns a real 404 |

Real-world (live, Restful-Booker):

| Real-world defect | Endpoint | Documented by |
|---|---|---|
| LIVE-DEF-01 — 201 on a health probe | `GET /ping` | TC-API-008 |
| LIVE-DEF-02 — 200 + reason on bad credentials | `POST /auth` | TC-API-008b; offline TC-API-004b shows the correct behavior |
| LIVE-DEF-03 — 201 on DELETE | `DELETE /booking/{id}` | TC-API-008c; offline TC-API-001e shows the correct 204 |
