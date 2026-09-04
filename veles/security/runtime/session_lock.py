from __future__ import annotations

from threading import RLock


class SecuritySessionLock:
    """
    Process-local VELES security session lock.

    Physical Security Device removal forces this lock into the locked
    state. Unlocking is always explicit and must be performed by the
    caller after successful Security Vault credential verification.

    Reconnecting a Security Device never changes this state.
    """

    def __init__(self) -> None:
        self._locked = True
        self._reason = "SECURITY DEVICE REQUIRED"
        self._lock = RLock()

    @property
    def is_locked(self) -> bool:
        with self._lock:
            return self._locked

    @property
    def reason(self) -> str:
        with self._lock:
            return self._reason

    def lock(
        self,
        reason: str = "SECURITY DEVICE REQUIRED",
    ) -> None:
        """
        Lock the VELES session.

        Locking is idempotent and may safely be called repeatedly.
        """
        with self._lock:
            self._locked = True
            self._reason = (
                str(reason).strip()
                or "SECURITY DEVICE REQUIRED"
            )

    def unlock(self) -> None:
        """
        Explicitly unlock the VELES session.

        Credential verification is intentionally NOT performed here.
        The caller must first successfully unlock the Security Vault.
        """
        with self._lock:
            self._locked = False
            self._reason = ""


security_session_lock = SecuritySessionLock()
