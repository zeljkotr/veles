"""
VELES Security Models

Data models for local and remote security inspection.

Security models are intentionally independent from the database
Resource ORM model.

The Resource Registry remains the canonical source of infrastructure
resources. Security results reference resource/target context through
metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class SecurityCheckResult:
    """
    Result of a single security check.

    Supports both local and remote inspection.

    Existing fields remain compatible with the original Security
    module. Target information is stored in metadata so no database
    migration is required at this stage.
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
    Complete security inspection report.

    A report represents one inspection target.

    Target information is stored in metadata so the same report
    structure can later represent local and remote resources.
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

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )
