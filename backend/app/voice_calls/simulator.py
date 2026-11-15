"""The default adapter: no account, no phone number, no network. The /call-demo page plays the same
prompts in the browser and sends the keys to /calls/sim/... with the family link, so judges and
families can try the whole call."""
from __future__ import annotations

import secrets

from .base import CallEvent


class SimulatorProvider:
    name = "simulator"
    needs_phone = False

    def place_call(self, attempt_id: int, phone_e164: str | None, callback_url: str) -> str:
        return f"sim-{attempt_id}-{secrets.token_hex(6)}"

    def parse_webhook(self, params: dict[str, str]) -> CallEvent:
        return CallEvent(params.get("call_id", ""), params.get("digit") or None, params.get("status"))

    def verify_signature(self, url: str, params: dict[str, str], headers: dict[str, str]) -> bool:
        # The simulator never receives provider webhooks: its keys arrive on /calls/sim/* behind the
        # family link instead, so the public webhook route always refuses it.
        return False
