"""Daily Bangla check-in calls (IVR). Provider-agnostic: app code talks to CallProvider only.

CALL_PROVIDER selects the adapter. "simulator" (the default) needs no account and never dials.
A real telephony adapter is added once the team has chosen a provider.
"""
from __future__ import annotations

import os

from .base import CallEvent, CallProvider
from .simulator import SimulatorProvider

_ADAPTERS: dict[str, type] = {"simulator": SimulatorProvider}


def provider() -> CallProvider:
    name = os.getenv("CALL_PROVIDER", "").strip().lower() or "simulator"
    return _ADAPTERS.get(name, SimulatorProvider)()


__all__ = ["CallEvent", "CallProvider", "SimulatorProvider", "provider"]
