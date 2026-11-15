"""The provider-agnostic interface every telephony adapter implements."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class CallEvent:
    provider_call_id: str
    digits: str | None       # the key pressed; None on a timeout
    status: str | None       # the provider's call status (e.g. "no-answer"), when it sends one


class CallProvider(Protocol):
    name: str
    needs_phone: bool  # the simulator never dials, so it needs no number

    def place_call(self, attempt_id: int, phone_e164: str | None, callback_url: str) -> str:
        """Start an outbound call; returns the provider's call id."""
        ...

    def parse_webhook(self, params: dict[str, str]) -> CallEvent:
        """Read a provider callback into a CallEvent."""
        ...

    def verify_signature(self, url: str, params: dict[str, str], headers: dict[str, str]) -> bool:
        """True only for a callback provably sent by the provider."""
        ...
