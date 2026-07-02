"""
Fixtures for rest-api-contract-qa.

Two tiers share these fixtures:

- Offline tier: the Booking API under test is started once per session on a
  random free loopback port (real HTTP, not Flask's test client), so every
  test exercises the full request/response stack exactly as an external
  consumer would. Deterministic, no network needed.
- Live tier (`-m live`): the same test patterns against Restful-Booker
  (https://restful-booker.herokuapp.com), a public API built for QA practice
  with live shared data and intentional real-world contract defects. Skips
  gracefully when the service is unreachable, so offline runs stay green.
"""

import json
import os
import sys
import threading
from pathlib import Path

import pytest
import requests
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from werkzeug.serving import make_server

SUITE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SUITE_ROOT))

from api.booking_api import DEMO_PASSWORD, DEMO_USERNAME, create_app, reset_store  # noqa: E402

SCHEMA_DIR = SUITE_ROOT / "schemas"
HTTP_TIMEOUT = 5  # seconds — no request may hang the suite


@pytest.fixture(scope="session")
def base_url():
    """Serve the Booking API on a random free port for the whole session."""
    server = make_server("127.0.0.1", 0, create_app())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join(timeout=5)


@pytest.fixture(scope="session")
def http():
    """Shared requests session (connection pooling across tests)."""
    with requests.Session() as session:
        session.request = _with_timeout(session.request)
        yield session


def _with_timeout(request_fn):
    def wrapper(method, url, **kwargs):
        kwargs.setdefault("timeout", HTTP_TIMEOUT)
        return request_fn(method, url, **kwargs)
    return wrapper


@pytest.fixture(autouse=True)
def _fresh_store():
    """Re-seed the booking store before every test (auth tokens survive)."""
    reset_store()
    yield


@pytest.fixture(scope="session")
def auth_headers(base_url, http):
    """Obtain a bearer token once via the real /auth/token endpoint."""
    resp = http.post(
        f"{base_url}/auth/token",
        json={"username": DEMO_USERNAME, "password": DEMO_PASSWORD},
    )
    assert resp.status_code == 200, f"Token issuance failed: {resp.text}"
    return {"Authorization": f"Bearer {resp.json()['token']}"}


@pytest.fixture(scope="session")
def schemas():
    """All JSON Schemas keyed by name (e.g. 'booking', 'error')."""
    return {
        path.name.removesuffix(".schema.json"): json.loads(path.read_text(encoding="utf-8"))
        for path in SCHEMA_DIR.glob("*.schema.json")
    }


@pytest.fixture(scope="session")
def validator_for(schemas):
    """Factory returning a Draft 2020-12 validator with cross-schema $refs resolved."""
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas.values()
    )

    def _build(name: str) -> Draft202012Validator:
        return Draft202012Validator(schemas[name], registry=registry)

    return _build


# ── Live tier: Restful-Booker ────────────────────────────────────────────────
LIVE_BASE_URL = os.environ.get("LIVE_API_BASE_URL", "https://restful-booker.herokuapp.com")
LIVE_HTTP_TIMEOUT = 30  # Heroku dynos can cold-start; be generous but bounded
LIVE_CREDENTIALS = {"username": "admin", "password": "password123"}  # documented demo creds


@pytest.fixture(scope="session")
def live_http():
    """Session for the live API: longer timeout, JSON Accept header
    (Restful-Booker answers 418 without it on some routes)."""
    with requests.Session() as session:
        session.headers["Accept"] = "application/json"
        original = session.request

        def with_live_timeout(method, url, **kwargs):
            kwargs.setdefault("timeout", LIVE_HTTP_TIMEOUT)
            return original(method, url, **kwargs)

        session.request = with_live_timeout
        yield session


@pytest.fixture(scope="session")
def live_api(live_http):
    """Base URL of the live service; skips the live tier when unreachable."""
    try:
        live_http.get(f"{LIVE_BASE_URL}/ping")
    except requests.RequestException as exc:
        pytest.skip(f"Restful-Booker unreachable — live tier skipped ({exc.__class__.__name__})")
    return LIVE_BASE_URL


@pytest.fixture(scope="session")
def live_credentials():
    return dict(LIVE_CREDENTIALS)


@pytest.fixture(scope="session")
def live_token(live_http, live_api):
    """Real auth token from the live /auth endpoint."""
    resp = live_http.post(f"{live_api}/auth", json=LIVE_CREDENTIALS)
    token = resp.json().get("token")
    if not token:
        pytest.skip(f"Live /auth did not issue a token: {resp.text}")
    return token


@pytest.fixture
def live_booking(live_http, live_api, live_token, live_booking_payload):
    """Create a booking on the live service; best-effort delete on teardown
    (the shared store also resets itself periodically)."""
    resp = live_http.post(f"{live_api}/booking", json=live_booking_payload)
    assert resp.status_code == 200, f"Live create failed: {resp.status_code} {resp.text}"
    booking_id = resp.json()["bookingid"]
    yield {"id": booking_id, "payload": live_booking_payload, "create_response": resp}
    try:
        live_http.delete(
            f"{live_api}/booking/{booking_id}",
            headers={"Cookie": f"token={live_token}"},
        )
    except requests.RequestException:
        pass  # periodic store reset cleans up anything we miss


@pytest.fixture
def live_booking_payload():
    """Fresh Restful-Booker-shaped payload (their schema, not ours)."""
    return {
        "firstname": "Anthony",
        "lastname": "Graves",
        "totalprice": 750,
        "depositpaid": True,
        "bookingdates": {"checkin": "2026-08-01", "checkout": "2026-08-05"},
        "additionalneeds": "Breakfast",
    }


@pytest.fixture(scope="session")
def valid_booking_payload():
    """A known-good creation payload; tests copy and mutate it, never edit it."""
    return {
        "guest_name": "Priya Raman",
        "guest_email": "priya.raman@example.com",
        "room_type": "deluxe",
        "check_in": "2026-10-01",
        "check_out": "2026-10-04",
        "total_price": 885.00,
    }
