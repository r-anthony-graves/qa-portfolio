"""
REST API Contract & Validation Test Suite
Project: rest-api-contract-qa
Tests validate CRUD behavior, JSON Schema contract compliance, negative-path
handling, bearer-token auth, and HTTP idempotency semantics of the Booking API,
plus positive detection of three seeded contract defects on the /legacy surface.
Domain: RESTful web service contract testing over real HTTP.
"""

import re

import pytest
from jsonschema.exceptions import ValidationError

# Payload fields the client controls; server adds booking_id/created_at.
CLIENT_FIELDS = ("guest_name", "guest_email", "room_type", "check_in", "check_out", "total_price")

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def create_booking(http, base_url, auth_headers, payload):
    resp = http.post(f"{base_url}/bookings", json=payload, headers=auth_headers)
    assert resp.status_code == 201, f"Setup create failed: {resp.status_code} {resp.text}"
    return resp


# ─────────────────────────────────────────────────────────────────────────────
# TC-API-001  CRUD Roundtrips
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.crud
class TestCrudRoundtrips:

    def test_create_returns_201_location_and_echoed_body(
        self, http, base_url, auth_headers, valid_booking_payload
    ):
        """TC-API-001 — REQ-API-01: POST /bookings returns 201, a Location header,
        and a representation echoing every client-supplied field."""
        resp = create_booking(http, base_url, auth_headers, valid_booking_payload)
        body = resp.json()
        assert resp.headers.get("Location") == f"/bookings/{body['booking_id']}"
        mismatches = {
            f: (valid_booking_payload[f], body[f])
            for f in CLIENT_FIELDS
            if body[f] != valid_booking_payload[f]
        }
        assert not mismatches, f"Created representation diverges from payload: {mismatches}"
        assert body["status"] == "pending", "Server must default status to 'pending'."

    def test_get_by_id_returns_created_representation(
        self, http, base_url, auth_headers, valid_booking_payload
    ):
        """TC-API-001b — REQ-API-01: GET /bookings/{id} returns exactly what POST created."""
        created = create_booking(http, base_url, auth_headers, valid_booking_payload).json()
        resp = http.get(f"{base_url}/bookings/{created['booking_id']}")
        assert resp.status_code == 200
        assert resp.json() == created, "GET representation differs from POST response."

    def test_list_includes_created_booking_and_accurate_count(
        self, http, base_url, auth_headers, valid_booking_payload
    ):
        """TC-API-001c — REQ-API-01: GET /bookings includes new bookings and count matches."""
        created = create_booking(http, base_url, auth_headers, valid_booking_payload).json()
        body = http.get(f"{base_url}/bookings").json()
        ids = [b["booking_id"] for b in body["bookings"]]
        assert created["booking_id"] in ids, "Created booking missing from collection."
        assert body["count"] == len(body["bookings"]), "count field disagrees with array length."

    def test_put_update_is_reflected_on_subsequent_get(
        self, http, base_url, auth_headers, valid_booking_payload
    ):
        """TC-API-001d — REQ-API-01: PUT replaces mutable fields; GET reflects the update."""
        created = create_booking(http, base_url, auth_headers, valid_booking_payload).json()
        updated_payload = {**valid_booking_payload, "room_type": "suite", "total_price": 1450.00}
        resp = http.put(
            f"{base_url}/bookings/{created['booking_id']}",
            json=updated_payload,
            headers=auth_headers,
        )
        assert resp.status_code == 200
        fetched = http.get(f"{base_url}/bookings/{created['booking_id']}").json()
        assert fetched["room_type"] == "suite"
        assert fetched["total_price"] == 1450.00
        assert fetched["booking_id"] == created["booking_id"], "Identity must be immutable."
        assert fetched["created_at"] == created["created_at"], "created_at must be immutable."

    def test_delete_returns_204_then_resource_is_gone(
        self, http, base_url, auth_headers, valid_booking_payload
    ):
        """TC-API-001e — REQ-API-01: DELETE returns 204; subsequent GET returns 404."""
        created = create_booking(http, base_url, auth_headers, valid_booking_payload).json()
        resp = http.delete(f"{base_url}/bookings/{created['booking_id']}", headers=auth_headers)
        assert resp.status_code == 204
        assert resp.text == "", "204 response must have an empty body."
        follow_up = http.get(f"{base_url}/bookings/{created['booking_id']}")
        assert follow_up.status_code == 404, "Deleted booking still retrievable."


# ─────────────────────────────────────────────────────────────────────────────
# TC-API-002  JSON Schema Contract Compliance
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.contract
class TestSchemaContracts:

    def test_health_endpoint_matches_health_schema(self, http, base_url, validator_for):
        """TC-API-002 — REQ-API-02: GET /health conforms to health.schema.json."""
        resp = http.get(f"{base_url}/health")
        assert resp.status_code == 200
        validator_for("health").validate(resp.json())

    def test_booking_collection_matches_list_schema(self, http, base_url, validator_for):
        """TC-API-002b — REQ-API-02: GET /bookings conforms to booking_list.schema.json
        (which validates every item against booking.schema.json via $ref)."""
        resp = http.get(f"{base_url}/bookings")
        assert resp.status_code == 200
        validator_for("booking_list").validate(resp.json())
        assert resp.json()["count"] >= 3, "Seeded store should hold at least 3 bookings."

    def test_single_booking_matches_booking_schema(self, http, base_url, validator_for):
        """TC-API-002c — REQ-API-02: GET /bookings/{id} conforms to booking.schema.json."""
        resp = http.get(f"{base_url}/bookings/BK-0001")
        assert resp.status_code == 200
        validator_for("booking").validate(resp.json())

    def test_token_response_matches_token_schema(
        self, http, base_url, validator_for
    ):
        """TC-API-002d — REQ-API-02: POST /auth/token success body conforms to token.schema.json."""
        from api.booking_api import DEMO_PASSWORD, DEMO_USERNAME

        resp = http.post(
            f"{base_url}/auth/token",
            json={"username": DEMO_USERNAME, "password": DEMO_PASSWORD},
        )
        assert resp.status_code == 200
        validator_for("token").validate(resp.json())

    def test_error_bodies_match_error_schema(self, http, base_url, validator_for):
        """TC-API-002e — REQ-API-02: 404 and 405 error bodies conform to error.schema.json."""
        not_found = http.get(f"{base_url}/bookings/BK-4242")
        assert not_found.status_code == 404
        validator_for("error").validate(not_found.json())

        wrong_method = http.patch(f"{base_url}/bookings/BK-0001", json={})
        assert wrong_method.status_code == 405
        validator_for("error").validate(wrong_method.json())


# ─────────────────────────────────────────────────────────────────────────────
# TC-API-003  Negative Testing — Invalid Input
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.negative
class TestNegativeInput:

    def test_missing_required_field_rejected_with_400_naming_the_field(
        self, http, base_url, auth_headers, valid_booking_payload
    ):
        """TC-API-003 — REQ-API-03: omitting a required field yields 400 and the
        error message names the missing field."""
        payload = {k: v for k, v in valid_booking_payload.items() if k != "guest_email"}
        resp = http.post(f"{base_url}/bookings", json=payload, headers=auth_headers)
        assert resp.status_code == 400
        assert "guest_email" in resp.json()["error"]["message"]

    def test_wrong_type_total_price_rejected_with_400(
        self, http, base_url, auth_headers, valid_booking_payload
    ):
        """TC-API-003b — REQ-API-03: total_price sent as a string is rejected, not coerced."""
        payload = {**valid_booking_payload, "total_price": "885.00"}
        resp = http.post(f"{base_url}/bookings", json=payload, headers=auth_headers)
        assert resp.status_code == 400
        assert "total_price" in resp.json()["error"]["message"]

    def test_malformed_json_body_rejected_with_400(self, http, base_url, auth_headers):
        """TC-API-003c — REQ-API-03: a syntactically invalid JSON body yields 400,
        not a 500 stack trace."""
        resp = http.post(
            f"{base_url}/bookings",
            data="{this is not json",
            headers={**auth_headers, "Content-Type": "application/json"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "MALFORMED_JSON"

    def test_checkout_on_or_before_checkin_rejected_with_400(
        self, http, base_url, auth_headers, valid_booking_payload
    ):
        """TC-API-003d — REQ-API-03: business rule — check_out must be after check_in."""
        payload = {**valid_booking_payload, "check_in": "2026-10-04", "check_out": "2026-10-04"}
        resp = http.post(f"{base_url}/bookings", json=payload, headers=auth_headers)
        assert resp.status_code == 400
        assert "check_out" in resp.json()["error"]["message"]

    def test_unknown_resource_404_and_unsupported_method_405(self, http, base_url):
        """TC-API-003e — REQ-API-03: unknown booking id → 404; PATCH (unsupported) → 405."""
        assert http.get(f"{base_url}/bookings/BK-4242").status_code == 404
        assert http.patch(f"{base_url}/bookings/BK-0001", json={}).status_code == 405


# ─────────────────────────────────────────────────────────────────────────────
# TC-API-004  Authentication & Authorization
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.auth
class TestAuthentication:

    def test_valid_credentials_issue_token(self, http, base_url):
        """TC-API-004 — REQ-API-04: valid credentials yield a bearer token."""
        from api.booking_api import DEMO_PASSWORD, DEMO_USERNAME

        resp = http.post(
            f"{base_url}/auth/token",
            json={"username": DEMO_USERNAME, "password": DEMO_PASSWORD},
        )
        assert resp.status_code == 200
        assert resp.json()["token_type"] == "bearer"

    def test_wrong_credentials_rejected_with_generic_401(self, http, base_url):
        """TC-API-004b — REQ-API-04: wrong credentials yield 401 with a generic message —
        no token, no hint of which field was wrong, no account detail."""
        resp = http.post(
            f"{base_url}/auth/token",
            json={"username": "qa_admin", "password": "wrong-password"},
        )
        assert resp.status_code == 401
        body = resp.json()
        assert "token" not in body
        message = body["error"]["message"]
        assert not EMAIL_PATTERN.search(message), "401 message must not expose account emails."
        assert "password" not in message.lower(), "401 message must not confirm the failing field."

    def test_write_without_token_rejected_with_401(
        self, http, base_url, valid_booking_payload
    ):
        """TC-API-004c — REQ-API-04: POST /bookings without a token is rejected."""
        resp = http.post(f"{base_url}/bookings", json=valid_booking_payload)
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "UNAUTHORIZED"

    def test_tampered_token_rejected_with_401(
        self, http, base_url, auth_headers, valid_booking_payload
    ):
        """TC-API-004d — REQ-API-04: a modified token is rejected — bearer tokens
        must be validated by value, not by shape."""
        real_token = auth_headers["Authorization"].removeprefix("Bearer ")
        flipped_last_char = "0" if real_token[-1] != "0" else "1"
        tampered = {"Authorization": f"Bearer {real_token[:-1]}{flipped_last_char}"}
        resp = http.post(f"{base_url}/bookings", json=valid_booking_payload, headers=tampered)
        assert resp.status_code == 401

    def test_valid_token_authorizes_all_write_methods(
        self, http, base_url, auth_headers, valid_booking_payload
    ):
        """TC-API-004e — REQ-API-04: one valid token authorizes POST, PUT, and DELETE."""
        created = create_booking(http, base_url, auth_headers, valid_booking_payload).json()
        put = http.put(
            f"{base_url}/bookings/{created['booking_id']}",
            json=valid_booking_payload,
            headers=auth_headers,
        )
        assert put.status_code == 200
        delete = http.delete(f"{base_url}/bookings/{created['booking_id']}", headers=auth_headers)
        assert delete.status_code == 204


# ─────────────────────────────────────────────────────────────────────────────
# TC-API-005  HTTP Idempotency Semantics
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.idempotency
class TestIdempotency:

    def test_put_is_idempotent(self, http, base_url, auth_headers, valid_booking_payload):
        """TC-API-005 — REQ-API-05: two identical PUTs return 200 with identical
        representations — replaying an update must not change the outcome."""
        created = create_booking(http, base_url, auth_headers, valid_booking_payload).json()
        url = f"{base_url}/bookings/{created['booking_id']}"
        payload = {**valid_booking_payload, "status": "confirmed"}
        first = http.put(url, json=payload, headers=auth_headers)
        second = http.put(url, json=payload, headers=auth_headers)
        assert first.status_code == second.status_code == 200
        assert first.json() == second.json(), "Replayed PUT produced a different representation."

    def test_delete_is_not_replayable(self, http, base_url, auth_headers, valid_booking_payload):
        """TC-API-005b — REQ-API-05: first DELETE → 204; replay → 404 (resource gone,
        and the server says so rather than pretending success)."""
        created = create_booking(http, base_url, auth_headers, valid_booking_payload).json()
        url = f"{base_url}/bookings/{created['booking_id']}"
        assert http.delete(url, headers=auth_headers).status_code == 204
        assert http.delete(url, headers=auth_headers).status_code == 404

    def test_post_is_not_idempotent(self, http, base_url, auth_headers, valid_booking_payload):
        """TC-API-005c — REQ-API-05: two identical POSTs create two distinct resources."""
        first = create_booking(http, base_url, auth_headers, valid_booking_payload).json()
        second = create_booking(http, base_url, auth_headers, valid_booking_payload).json()
        assert first["booking_id"] != second["booking_id"], (
            "POST must mint a new resource per request."
        )


# ─────────────────────────────────────────────────────────────────────────────
# TC-API-006  Seeded Defect Detection (/legacy surface)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.defects
class TestSeededDefectDetection:

    def test_DEF_API_01_legacy_record_violates_booking_schema(
        self, http, base_url, validator_for
    ):
        """TC-API-006 — REQ-API-06: the legacy record BK-9001 (missing status,
        total_price as string) MUST fail booking-schema validation — proving the
        contract check can detect drift."""
        resp = http.get(f"{base_url}/legacy/bookings/BK-9001")
        assert resp.status_code == 200
        body = resp.json()
        with pytest.raises(ValidationError):
            validator_for("booking").validate(body)
        assert "status" not in body, "Seeded defect changed: 'status' should be absent."
        assert isinstance(body["total_price"], str), (
            "Seeded defect changed: total_price should be a string."
        )

    def test_DEF_API_02_legacy_login_error_leaks_pii(self, http, base_url):
        """TC-API-006b — REQ-API-06: the legacy login failure message MUST be
        detected leaking an account email and internal credential detail."""
        resp = http.post(
            f"{base_url}/legacy/auth/login",
            json={"username": "qa_admin", "password": "wrong-password"},
        )
        assert resp.status_code == 401
        message = resp.json()["error"]["message"]
        leaked_emails = EMAIL_PATTERN.findall(message)
        assert leaked_emails, "Seeded PII leak not detected in legacy error message."
        assert "hash" in message.lower(), "Seeded internal-detail leak not detected."

    def test_DEF_API_03_legacy_unknown_id_returns_soft_404(self, http, base_url):
        """TC-API-006c — REQ-API-06: the legacy endpoint MUST be caught answering an
        unknown id with HTTP 200 + error body (soft 404) — the modern endpoint
        answers the same case with a real 404."""
        legacy = http.get(f"{base_url}/legacy/bookings/BK-4242")
        assert legacy.status_code == 200, "Seeded defect changed: expected soft-404 (HTTP 200)."
        assert legacy.json() == {"error": "booking not found"}
        modern = http.get(f"{base_url}/bookings/BK-4242")
        assert modern.status_code == 404, "Modern endpoint regressed: must return a real 404."
