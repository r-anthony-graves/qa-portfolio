"""
Live tier — Restful-Booker (https://restful-booker.herokuapp.com)
Project: rest-api-contract-qa
The same contract-testing patterns as the offline tier, but against a live
public API with real shared data: CRUD roundtrips on bookings this suite
creates itself, JSON Schema validation of live responses, token auth, and —
the live counterpart to the offline tier's seeded defects — positive
documentation of the service's *intentional real-world contract defects*:

  LIVE-DEF-01  GET /ping answers 201 Created for a read-only health probe
  LIVE-DEF-02  POST /auth with bad credentials answers 200 + {"reason": ...},
               not 401 — a real account-probing enabler
  LIVE-DEF-03  DELETE answers 201 Created instead of 204/200

All tests skip cleanly when the service is unreachable (see `live_api`), and
transient network flakiness is absorbed by pytest-rerunfailures.
"""

import pytest

pytestmark = [pytest.mark.live, pytest.mark.flaky(reruns=2, reruns_delay=2)]


# ─────────────────────────────────────────────────────────────────────────────
# TC-API-007  Live CRUD & Contract (Restful-Booker)
# ─────────────────────────────────────────────────────────────────────────────
class TestLiveCrudAndContract:

    def test_live_create_roundtrip_and_envelope_schema(
        self, live_http, live_api, live_booking, validator_for
    ):
        """TC-API-007 — REQ-API-07: POST /booking echoes the payload inside a
        {bookingid, booking} envelope that validates against the live schema."""
        body = live_booking["create_response"].json()
        validator_for("live_create_response").validate(body)
        assert body["booking"] == live_booking["payload"], (
            "Live create response diverges from the submitted payload."
        )

    def test_live_get_by_id_matches_payload_and_schema(
        self, live_http, live_api, live_booking, validator_for
    ):
        """TC-API-007b — REQ-API-07: GET /booking/{id} returns the stored booking,
        conforming to live_booking.schema.json."""
        resp = live_http.get(f"{live_api}/booking/{live_booking['id']}")
        assert resp.status_code == 200
        validator_for("live_booking").validate(resp.json())
        assert resp.json() == live_booking["payload"]

    def test_live_collection_lists_created_booking(self, live_http, live_api, live_booking):
        """TC-API-007c — REQ-API-07: GET /booking returns an id index that
        includes the booking this test created (shared live store: only shape
        and membership are asserted, never other users' content)."""
        resp = live_http.get(f"{live_api}/booking")
        assert resp.status_code == 200
        ids = [entry["bookingid"] for entry in resp.json()]
        assert live_booking["id"] in ids, "Created booking missing from live index."

    def test_live_put_full_update_with_token(
        self, live_http, live_api, live_booking, live_token, live_booking_payload
    ):
        """TC-API-007d — REQ-API-07: PUT with a Cookie token replaces the booking;
        the change is visible on a subsequent GET."""
        updated = {**live_booking_payload, "firstname": "Ray", "totalprice": 990}
        resp = live_http.put(
            f"{live_api}/booking/{live_booking['id']}",
            json=updated,
            headers={"Cookie": f"token={live_token}"},
        )
        assert resp.status_code == 200, f"Live PUT failed: {resp.status_code} {resp.text}"
        fetched = live_http.get(f"{live_api}/booking/{live_booking['id']}").json()
        assert fetched["firstname"] == "Ray"
        assert fetched["totalprice"] == 990

    def test_live_patch_updates_only_the_target_field(
        self, live_http, live_api, live_booking, live_token
    ):
        """TC-API-007e — REQ-API-07: PATCH changes the submitted field and
        leaves every other field untouched."""
        resp = live_http.patch(
            f"{live_api}/booking/{live_booking['id']}",
            json={"firstname": "Ray"},
            headers={"Cookie": f"token={live_token}"},
        )
        assert resp.status_code == 200, f"Live PATCH failed: {resp.status_code} {resp.text}"
        fetched = live_http.get(f"{live_api}/booking/{live_booking['id']}").json()
        assert fetched["firstname"] == "Ray"
        untouched = {k: v for k, v in live_booking["payload"].items() if k != "firstname"}
        assert {k: fetched[k] for k in untouched} == untouched, (
            "PATCH modified fields it was not given."
        )

    def test_live_write_without_token_is_rejected(
        self, live_http, live_api, live_booking, live_booking_payload
    ):
        """TC-API-007f — REQ-API-07: PUT/DELETE without a token are refused (403)
        and the booking survives unchanged."""
        put = live_http.put(f"{live_api}/booking/{live_booking['id']}", json=live_booking_payload)
        delete = live_http.delete(f"{live_api}/booking/{live_booking['id']}")
        assert put.status_code == 403
        assert delete.status_code == 403
        still_there = live_http.get(f"{live_api}/booking/{live_booking['id']}")
        assert still_there.status_code == 200, "Unauthenticated write mutated the booking."

    def test_live_unknown_booking_id_returns_404(self, live_http, live_api):
        """TC-API-007g — REQ-API-07: an id that cannot exist yields a real 404
        (unlike the offline tier's seeded soft-404 defect)."""
        resp = live_http.get(f"{live_api}/booking/999999999")
        assert resp.status_code == 404

    def test_live_auth_issues_token_for_documented_credentials(
        self, live_http, live_api, live_credentials
    ):
        """TC-API-007h — REQ-API-07: POST /auth with the documented demo
        credentials returns a usable token."""
        resp = live_http.post(f"{live_api}/auth", json=live_credentials)
        assert resp.status_code == 200
        assert resp.json().get("token"), f"No token in live auth response: {resp.text}"


# ─────────────────────────────────────────────────────────────────────────────
# TC-API-008  Real-World Defect Documentation (live service quirks)
# ─────────────────────────────────────────────────────────────────────────────
class TestLiveRealWorldDefects:

    def test_LIVE_DEF_01_ping_returns_201_for_a_health_probe(self, live_http, live_api):
        """TC-API-008 — REQ-API-07: GET /ping answers 201 Created — a read-only
        health probe claiming a resource was created. Documented as a real
        contract defect; this test fails the day the service fixes it."""
        resp = live_http.get(f"{live_api}/ping")
        assert resp.status_code == 201, (
            f"/ping now returns {resp.status_code} — LIVE-DEF-01 may have been fixed upstream; "
            "update the contract docs."
        )

    def test_LIVE_DEF_02_bad_credentials_return_200_not_401(self, live_http, live_api):
        """TC-API-008b — REQ-API-07: failed login answers HTTP 200 with
        {"reason": "Bad credentials"} instead of 401 — the offline tier's
        TC-API-004b shows the correct behavior for the same case."""
        resp = live_http.post(
            f"{live_api}/auth",
            json={"username": "admin", "password": "definitely-wrong"},
        )
        assert resp.status_code == 200, (
            f"Live /auth now returns {resp.status_code} on bad credentials — "
            "LIVE-DEF-02 may have been fixed upstream; update the contract docs."
        )
        assert resp.json() == {"reason": "Bad credentials"}
        assert "token" not in resp.json()

    def test_LIVE_DEF_03_delete_returns_201_instead_of_204(
        self, live_http, live_api, live_token, live_booking_payload
    ):
        """TC-API-008c — REQ-API-07: DELETE answers 201 Created — the wrong
        success code for a removal (offline tier's TC-API-001e shows 204).
        The booking is created by this test purely to be deleted."""
        created = live_http.post(f"{live_api}/booking", json=live_booking_payload)
        assert created.status_code == 200
        booking_id = created.json()["bookingid"]

        resp = live_http.delete(
            f"{live_api}/booking/{booking_id}",
            headers={"Cookie": f"token={live_token}"},
        )
        assert resp.status_code == 201, (
            f"Live DELETE now returns {resp.status_code} — LIVE-DEF-03 may have been fixed "
            "upstream; update the contract docs."
        )
        gone = live_http.get(f"{live_api}/booking/{booking_id}")
        assert gone.status_code == 404, "Deleted live booking is still retrievable."
