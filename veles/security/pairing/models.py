from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


PAIRING_STATE_VERSION = 1


class PairingState(StrEnum):
    UNPAIRED = "unpaired"
    PAIRING = "pairing"
    PAIRED = "paired"


@dataclass(frozen=True)
class PairingRecord:
    """
    Persistent pairing record for one VELES Security Device.
    """

    device_id: str
    identity_version: int
    provider: str
    state: PairingState
