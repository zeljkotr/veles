"""
VELES Mobile Models

Data models for VELES Mobile devices and protocol responses.

These models intentionally contain no secret values.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict


@dataclass
class MobileDevice:
    """
    VELES Mobile device identity.

    The device_id is owned by the Mobile device.
    VELES must never invent or hardcode it.
    """

    device_id: str

    name: str = ""

    protocol_version: str = "1"

    status: str = "unknown"

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    last_seen: str = ""


@dataclass
class MobileResponse:
    """
    Standard response exchanged between VELES and Mobile.
    """

    status: str = "unknown"

    message: str = ""

    timestamp: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    data: Dict[str, Any] = field(
        default_factory=dict
    )
