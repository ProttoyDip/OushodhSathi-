"""WhatsApp Cloud API: send the check-in messages and verify webhook signatures. Read from Meta's docs:

- Send: POST https://graph.facebook.com/<API_VERSION>/<PHONE_NUMBER_ID>/messages, Bearer token, body
  {"messaging_product": "whatsapp", "recipient_type": "individual", "to": ..., "type": ...}; the response
  carries {"messages": [{"id": "wamid..."}]}.
  https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/send-messages.md
- Template message (type "template", template {name, language {code}}):
  https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/utility-templates/utility-templates.md
- Interactive reply buttons (type "interactive", interactive {type "button", body {text}, action {buttons:
  [{type "reply", reply {id, title}}]}}), v27.0 in the example:
  https://developers.facebook.com/docs/whatsapp/cloud-api/messages/interactive-reply-buttons-messages
- Webhooks: GET verification with hub.mode / hub.verify_token / hub.challenge; POST bodies signed in
  X-Hub-Signature-256 as "sha256=" + SHA256 HMAC with the app secret:
  https://developers.facebook.com/docs/graph-api/webhooks/getting-started
Keys (names in backend/.env.example): WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_APP_SECRET,
WHATSAPP_VERIFY_TOKEN; optional WHATSAPP_API_VERSION (default v27.0).
The family's number goes only to Meta, only after recorded consent; message text never names anyone.
"""
from __future__ import annotations

import hashlib
import hmac
import os

import httpx

from .flow import TEMPLATE_LANGUAGE, TEMPLATE_NAME, Out

TIMEOUT_S = 15


def _env(name: str) -> str:
    return os.getenv(name, "").strip()


def configured() -> bool:
    return bool(_env("WHATSAPP_TOKEN") and _env("WHATSAPP_PHONE_NUMBER_ID") and _env("WHATSAPP_APP_SECRET"))


class SendFailed(RuntimeError):
    pass


def payload(to: str, out: Out) -> dict:
    """The Messages API body for one check-in message. Pure; tested."""
    base = {"messaging_product": "whatsapp", "recipient_type": "individual", "to": to}
    if out.template:
        return {**base, "type": "template",
                "template": {"name": _env("WHATSAPP_TEMPLATE") or TEMPLATE_NAME, "language": {"code": TEMPLATE_LANGUAGE}}}
    if out.buttons:
        return {**base, "type": "interactive", "interactive": {
            "type": "button", "body": {"text": out.text},
            "action": {"buttons": [{"type": "reply", "reply": {"id": i, "title": t}} for i, t in out.buttons]}}}
    return {**base, "type": "text", "text": {"body": out.text}}


def send(to: str, out: Out, client: httpx.Client | None = None) -> str:
    """-> the WhatsApp message id (wamid)."""
    version = _env("WHATSAPP_API_VERSION") or "v27.0"
    url = f"https://graph.facebook.com/{version}/{_env('WHATSAPP_PHONE_NUMBER_ID')}/messages"
    c = client or httpx.Client(timeout=TIMEOUT_S)
    try:
        r = c.post(url, json=payload(to, out), headers={"Authorization": f"Bearer {_env('WHATSAPP_TOKEN')}"})
        r.raise_for_status()
        return r.json()["messages"][0]["id"]
    except (httpx.HTTPError, KeyError, IndexError, ValueError) as e:
        raise SendFailed(type(e).__name__) from e


def verify_signature(raw_body: bytes, header: str | None) -> bool:
    secret = _env("WHATSAPP_APP_SECRET")
    if not secret or not header or not header.startswith("sha256="):
        return False
    want = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(want, header.removeprefix("sha256="))


def verify_subscription(mode: str | None, token: str | None) -> bool:
    expected = _env("WHATSAPP_VERIFY_TOKEN")
    return mode == "subscribe" and bool(expected) and hmac.compare_digest(expected, token or "")
