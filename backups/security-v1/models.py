"""
VELES Security Models

Data models for local security inspection.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class SecurityCheckResult:
    """
    Result of a single security check.
    """

    check_type: str

    status: str = "unknown"

    message: str = ""

    timestamp: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    data: Any = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class SecurityReport:
    """
    Complete security state of the local VELES system.
    """

    status: str = "unknown"

    checks: List[SecurityCheckResult] = field(
        default_factory=list
    )

    timestamp: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    summary: Dict[str, Any] = field(
        default_factory=dict
    )