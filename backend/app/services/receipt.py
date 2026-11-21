import base64
import hashlib
import hmac
import json
import time
from flask import current_app

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def issue_receipt(payload: dict) -> str:
    """Create a compact HMAC-SHA256-signed receipt; never trust a client-supplied score."""
    secret = current_app.config["SECRET_KEY"].encode("utf-8")
    body = _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signature = _b64(hmac.new(secret, body.encode("ascii"), hashlib.sha256).digest())
    return f"{body}.{signature}"

def verify_receipt(token: str) -> dict | None:
    try:
        body, signature = token.split(".", 1)
        secret = current_app.config["SECRET_KEY"].encode("utf-8")
        expected = _b64(hmac.new(secret, body.encode("ascii"), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            return None
        padded = body + "=" * (-len(body) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
        if not isinstance(payload, dict) or payload.get("v") != 2 or payload.get("scope") != "daily":
            return None
        issued_at = int(payload.get("issuedAt", 0))
        now = int(time.time() * 1000)
        if issued_at > now + 60_000 or now - issued_at > current_app.config["RECEIPT_MAX_AGE_MS"]:
            return None
        return payload
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None
