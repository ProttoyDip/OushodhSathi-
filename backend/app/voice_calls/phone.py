"""Phone numbers: Bangladeshi mobile numbers only, encrypted at rest, shown masked.

A number is stored only after the family's recorded consent, only when a real telephony provider is
on, and it goes only to that provider: never to a model, never into logs, never in full in an export.
Encryption: Fernet (AES-128-CBC + HMAC-SHA256) from the `cryptography` package,
https://cryptography.io/en/latest/fernet/ ; key in PHONE_ENCRYPTION_KEY (Fernet.generate_key()).
"""
from __future__ import annotations

import os
import re

from cryptography.fernet import Fernet, InvalidToken

# Bangladeshi mobile numbers: +880, then 1, an operator digit 3-9, then 8 digits (013... to 019...)
_BD_MOBILE = re.compile(r"^\+8801[3-9]\d{8}$")


class PhoneStorageUnavailable(RuntimeError):
    pass


def normalise(raw: str) -> str | None:
    digits = re.sub(r"[\s\-()]", "", raw or "")
    if digits.startswith("01"):
        digits = "+88" + digits
    elif digits.startswith("8801"):
        digits = "+" + digits
    return digits if _BD_MOBILE.match(digits) else None


def _fernet() -> Fernet:
    key = os.getenv("PHONE_ENCRYPTION_KEY", "").strip()
    if not key:
        raise PhoneStorageUnavailable("PHONE_ENCRYPTION_KEY is not set")
    return Fernet(key.encode())


def encrypt(phone_e164: str) -> str:
    return _fernet().encrypt(phone_e164.encode()).decode()


def decrypt(token: str | None) -> str | None:
    if not token:
        return None
    try:
        return _fernet().decrypt(token.encode()).decode()
    except (InvalidToken, PhoneStorageUnavailable, ValueError):
        return None


def masked(phone_e164: str | None) -> str | None:
    return f"{phone_e164[:6]}•••••{phone_e164[-3:]}" if phone_e164 else None
