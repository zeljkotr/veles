from __future__ import annotations

from dataclasses import dataclass
import hashlib


IDENTITY_VERSION = 1


@dataclass(frozen=True)
class IdentityEvidence:
    """
    Hardware identity evidence collected by a device-specific provider.

    Evidence is deliberately separated from the final VELES device ID.
    """

    source: str
    primary: tuple[tuple[str, str], ...]
    secondary: tuple[tuple[str, str], ...]
    descriptive: tuple[tuple[str, str], ...]
    location: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class SecurityDeviceIdentity:
    """
    Hardware-independent VELES Security Device identity.
    """

    device_id: str
    identity_version: int
    provider: str


def _canonicalize(
    evidence: IdentityEvidence,
) -> bytes:
    parts: list[str] = []

    for category, values in (
        ("primary", evidence.primary),
        ("secondary", evidence.secondary),
    ):
        for key, value in sorted(values):
            normalized_key = key.strip().lower()
            normalized_value = value.strip()

            if not normalized_value:
                continue

            parts.append(
                f"{category}:{normalized_key}={normalized_value}"
            )

    return "\n".join(parts).encode("utf-8")


def generate_device_identity(
    evidence: IdentityEvidence,
) -> SecurityDeviceIdentity:
    """
    Generate a deterministic VELES identity from validated
    hardware identity evidence.

    Location and descriptive information are intentionally excluded.
    """

    canonical = _canonicalize(evidence)

    if not canonical:
        raise ValueError(
            "Insufficient hardware identity evidence"
        )

    digest = hashlib.sha256(canonical).hexdigest()

    return SecurityDeviceIdentity(
        device_id=f"veles-{digest}",
        identity_version=IDENTITY_VERSION,
        provider=evidence.source,
    )
