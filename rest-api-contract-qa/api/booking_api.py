"""
Booking REST API — the system under test for rest-api-contract-qa.

A deliberately small Flask service exposing a hotel-booking resource with
bearer-token auth, so the test suite can exercise CRUD, contract (JSON Schema),
negative, auth, and idempotency scenarios over real HTTP.

The `/legacy` blueprint contains three SEEDED DEFECTS the suite must positively
detect (the portfolio's error-seeding theme — checks are only trustworthy if
they can fail):

  DEF-API-01  GET  /legacy/bookings/BK-9001   → schema drift (missing `status`,
              `total_price` serialized as a string)
  DEF-API-02  POST /legacy/auth/login          → 401 error message leaks the
              account email and internal hash detail (PII in error body)
  DEF-API-03  GET  /legacy/bookings/<unknown>  → HTTP 200 with an error body
              instead of 404 (wrong status code)

Security note: credentials and tokens here are demo-only fixtures for a local,
loopback-bound test server. Nothing in this module is production auth.
"""

from __future__ import annotations

import copy
import logging
import secrets
from datetime import date, datetime, timezone
from typing import Any

from flask import Blueprint, Flask, jsonify, request

logger = logging.getLogger("booking-api")

# ── Demo credentials & token store (module-level, reset via reset_store) ────
DEMO_USERNAME = "qa_admin"
DEMO_PASSWORD = "portfolio-demo-2026"
TOKEN_TTL_SECONDS = 3600

_valid_tokens: set[str] = set()

# ── Booking domain rules ─────────────────────────────────────────────────────
ROOM_TYPES = {"standard", "deluxe", "suite"}
STATUSES = {"pending", "confirmed", "cancelled"}
REQUIRED_FIELDS = (
    "guest_name", "guest_email", "room_type", "check_in", "check_out", "total_price",
)

_SEED_BOOKINGS: dict[str, dict[str, Any]] = {
    "BK-0001": {
        "booking_id": "BK-0001",
        "guest_name": "Amara Osei",
        "guest_email": "amara.osei@example.com",
        "room_type": "deluxe",
        "check_in": "2026-08-10",
        "check_out": "2026-08-14",
        "total_price": 1180.00,
        "status": "confirmed",
        "created_at": "2026-06-01T09:15:00+00:00",
    },
    "BK-0002": {
        "booking_id": "BK-0002",
        "guest_name": "Luis Herrera",
        "guest_email": "luis.herrera@example.com",
        "room_type": "standard",
        "check_in": "2026-09-02",
        "check_out": "2026-09-05",
        "total_price": 447.00,
        "status": "pending",
        "created_at": "2026-06-12T14:40:00+00:00",
    },
    "BK-0003": {
        "booking_id": "BK-0003",
        "guest_name": "Mei Nakamura",
        "guest_email": "mei.nakamura@example.com",
        "room_type": "suite",
        "check_in": "2026-07-20",
        "check_out": "2026-07-27",
        "total_price": 3290.00,
        "status": "confirmed",
        "created_at": "2026-05-28T18:05:00+00:00",
    },
}

_bookings: dict[str, dict[str, Any]] = {}
_id_counter: int = 1000


def reset_store() -> None:
    """Restore the booking store to its seeded state (auth tokens survive)."""
    global _id_counter
    _bookings.clear()
    _bookings.update(copy.deepcopy(_SEED_BOOKINGS))
    _id_counter = 1000


reset_store()


# ── Helpers ──────────────────────────────────────────────────────────────────
def _error(status: int, code: str, message: str):
    return jsonify({"error": {"code": code, "message": message}}), status


def _require_auth() -> tuple | None:
    """Return an error response if the request lacks a valid bearer token."""
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return _error(401, "UNAUTHORIZED", "Missing bearer token.")
    if header.removeprefix("Bearer ") not in _valid_tokens:
        return _error(401, "UNAUTHORIZED", "Invalid or expired token.")
    return None


def _validate_booking_payload(payload: dict[str, Any]) -> list[str]:
    """Return a list of validation error messages (empty when valid)."""
    errors = [f"'{f}' is required" for f in REQUIRED_FIELDS if f not in payload]
    if errors:
        return errors

    if not isinstance(payload["guest_name"], str) or not payload["guest_name"].strip():
        errors.append("'guest_name' must be a non-empty string")
    if not isinstance(payload["guest_email"], str) or "@" not in payload["guest_email"]:
        errors.append("'guest_email' must be a valid email address")
    if payload["room_type"] not in ROOM_TYPES:
        errors.append(f"'room_type' must be one of {sorted(ROOM_TYPES)}")
    if not isinstance(payload["total_price"], (int, float)) or isinstance(payload["total_price"], bool):
        errors.append("'total_price' must be a number")
    elif payload["total_price"] <= 0:
        errors.append("'total_price' must be greater than 0")
    if payload.get("status", "pending") not in STATUSES:
        errors.append(f"'status' must be one of {sorted(STATUSES)}")

    try:
        check_in = date.fromisoformat(str(payload["check_in"]))
        check_out = date.fromisoformat(str(payload["check_out"]))
    except (TypeError, ValueError):
        errors.append("'check_in' and 'check_out' must be ISO dates (YYYY-MM-DD)")
    else:
        if check_out <= check_in:
            errors.append("'check_out' must be after 'check_in'")
    return errors


def _next_booking_id() -> str:
    global _id_counter
    _id_counter += 1
    return f"BK-{_id_counter}"


# ── Legacy blueprint: the three seeded defects ───────────────────────────────
legacy = Blueprint("legacy", __name__, url_prefix="/legacy")


@legacy.get("/bookings/<booking_id>")
def legacy_get_booking(booking_id: str):
    if booking_id == "BK-9001":
        # DEF-API-01 (seeded): schema drift — `status` missing, `total_price`
        # serialized as a string. Must FAIL booking.schema.json validation.
        return jsonify({
            "booking_id": "BK-9001",
            "guest_name": "Legacy Import",
            "guest_email": "legacy.import@example.com",
            "room_type": "standard",
            "check_in": "2026-01-05",
            "check_out": "2026-01-08",
            "total_price": "450.00",
            "created_at": "2019-11-30T00:00:00+00:00",
        })
    # DEF-API-03 (seeded): unknown resource answered with 200 + error body
    # instead of 404 — the classic "soft 404" contract violation.
    return jsonify({"error": "booking not found"}), 200


@legacy.post("/auth/login")
def legacy_login():
    payload = request.get_json(silent=True) or {}
    # DEF-API-02 (seeded): failure message echoes the account email and
    # internal credential detail — PII/internal leakage in an error body.
    return _error(
        401,
        "LOGIN_FAILED",
        f"Invalid password for jane.doe@example.com "
        f"(stored hash sha1:5baa61e4..., attempt from {request.remote_addr}) "
        f"— username tried: {payload.get('username', '<none>')}",
    )


# ── Application factory ──────────────────────────────────────────────────────
def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(legacy)

    @app.errorhandler(404)
    def not_found(_):
        return _error(404, "NOT_FOUND", "The requested resource does not exist.")

    @app.errorhandler(405)
    def method_not_allowed(_):
        return _error(405, "METHOD_NOT_ALLOWED", "HTTP method not supported for this resource.")

    @app.get("/health")
    def health():
        return jsonify({
            "status": "ok",
            "service": "booking-api",
            "version": "1.0.0",
            "time": datetime.now(timezone.utc).isoformat(),
        })

    @app.post("/auth/token")
    def issue_token():
        payload = request.get_json(silent=True)
        if payload is None or "username" not in payload or "password" not in payload:
            return _error(400, "VALIDATION_ERROR", "'username' and 'password' are required.")
        if payload["username"] != DEMO_USERNAME or payload["password"] != DEMO_PASSWORD:
            logger.warning("Failed login attempt for user %r", payload.get("username"))
            # Deliberately generic: no hint of which field was wrong (contrast DEF-API-02).
            return _error(401, "UNAUTHORIZED", "Invalid credentials.")
        token = secrets.token_hex(16)
        _valid_tokens.add(token)
        return jsonify({"token": token, "token_type": "bearer", "expires_in": TOKEN_TTL_SECONDS})

    @app.get("/bookings")
    def list_bookings():
        items = sorted(_bookings.values(), key=lambda b: b["booking_id"])
        return jsonify({"bookings": items, "count": len(items)})

    @app.get("/bookings/<booking_id>")
    def get_booking(booking_id: str):
        booking = _bookings.get(booking_id)
        if booking is None:
            return _error(404, "NOT_FOUND", f"Booking '{booking_id}' does not exist.")
        return jsonify(booking)

    @app.post("/bookings")
    def create_booking():
        if (denied := _require_auth()) is not None:
            return denied
        payload = request.get_json(silent=True)
        if payload is None:
            return _error(400, "MALFORMED_JSON", "Request body must be valid JSON.")
        if errors := _validate_booking_payload(payload):
            return _error(400, "VALIDATION_ERROR", "; ".join(errors))

        booking = {
            "booking_id": _next_booking_id(),
            "guest_name": payload["guest_name"],
            "guest_email": payload["guest_email"],
            "room_type": payload["room_type"],
            "check_in": payload["check_in"],
            "check_out": payload["check_out"],
            "total_price": float(payload["total_price"]),
            "status": payload.get("status", "pending"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        _bookings[booking["booking_id"]] = booking
        logger.info("Created booking %s", booking["booking_id"])
        response = jsonify(booking)
        response.headers["Location"] = f"/bookings/{booking['booking_id']}"
        return response, 201

    @app.put("/bookings/<booking_id>")
    def update_booking(booking_id: str):
        if (denied := _require_auth()) is not None:
            return denied
        existing = _bookings.get(booking_id)
        if existing is None:
            return _error(404, "NOT_FOUND", f"Booking '{booking_id}' does not exist.")
        payload = request.get_json(silent=True)
        if payload is None:
            return _error(400, "MALFORMED_JSON", "Request body must be valid JSON.")
        if errors := _validate_booking_payload(payload):
            return _error(400, "VALIDATION_ERROR", "; ".join(errors))

        # Full replace of mutable fields; identity and created_at are immutable,
        # which is what makes PUT idempotent here.
        existing.update({
            "guest_name": payload["guest_name"],
            "guest_email": payload["guest_email"],
            "room_type": payload["room_type"],
            "check_in": payload["check_in"],
            "check_out": payload["check_out"],
            "total_price": float(payload["total_price"]),
            "status": payload.get("status", existing["status"]),
        })
        return jsonify(existing)

    @app.delete("/bookings/<booking_id>")
    def delete_booking(booking_id: str):
        if (denied := _require_auth()) is not None:
            return denied
        if booking_id not in _bookings:
            return _error(404, "NOT_FOUND", f"Booking '{booking_id}' does not exist.")
        del _bookings[booking_id]
        logger.info("Deleted booking %s", booking_id)
        return "", 204

    return app


if __name__ == "__main__":
    # Manual exploration only; the test suite starts its own server thread.
    create_app().run(host="127.0.0.1", port=5057, debug=True)
