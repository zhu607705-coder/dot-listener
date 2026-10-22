"""Pure protocol helpers only. No subscriptions, network delivery or DNS pinning.
Do not advertise MCP Events based on these helpers alone.
"""
import base64
import hashlib
import hmac
import ipaddress
import json
from urllib.parse import urlsplit

MAX_EVENT_BYTES = 256 * 1024

def signing_key(secret: str) -> bytes:
    if not secret.startswith("whsec_"): raise ValueError("Missing whsec_ prefix")
    try:
        key = base64.b64decode(secret[6:], validate=True)
    except Exception:
        raise ValueError("Invalid signing secret") from None
    if not 24 <= len(key) <= 64: raise ValueError("Key must contain 24–64 bytes")
    return key

def serialize_event(event: dict) -> bytes:
    required = {"eventId", "name", "timestamp", "data", "cursor"}
    if set(event) != required or not isinstance(event["data"], dict):
        raise ValueError("Invalid event envelope")
    body = json.dumps(event, ensure_ascii=False, separators=(",", ":")).encode()
    if len(body) > MAX_EVENT_BYTES: raise ValueError("Event too large")
    return body

def sign_headers(event_id: str, subscription_id: str, body: bytes, secret: str, timestamp: int):
    if len(body) > MAX_EVENT_BYTES: raise ValueError("Event too large")
    if any(c in event_id + subscription_id for c in "\r\n"): raise ValueError("Invalid header value")
    message = f"{event_id}.{timestamp}.".encode() + body
    signature = base64.b64encode(hmac.new(signing_key(secret), message, hashlib.sha256).digest()).decode()
    return {"Content-Type": "application/json", "webhook-id": event_id,
            "webhook-timestamp": str(timestamp), "webhook-signature": "v1," + signature,
            "X-MCP-Subscription-Id": subscription_id}

def validate_callback_shape(url: str, allowed_hosts: set[str]):
    """First gate only. Live sender MUST pin validated public IPs at connect time."""
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.username or parts.password or parts.fragment
        or not parts.hostname or parts.hostname not in allowed_hosts or parts.port not in (None, 443)):
        raise ValueError("Callback URL is not explicitly allowed")
    try:
        address = ipaddress.ip_address(parts.hostname)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError("Non-public destinations are blocked")
    return parts.hostname
