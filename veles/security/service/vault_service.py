from __future__ import annotations

from pathlib import Path

from ..pairing.manager import (
    DeviceNotFoundError,
    PairingError,
    PairingManager,
)
from ..pairing.models import PairingState
from ..runtime.registry import SecurityDeviceRegistry
from ..vault.vault import Vault


class SecurityVaultError(RuntimeError):
    """
    Base exception for Security Device / Vault lifecycle failures.
    """


class SecurityVaultNotPairedError(SecurityVaultError):
    """
    Raised when Vault access is attempted without pairing.
    """


class SecurityVaultDeviceUnavailableError(SecurityVaultError):
    """
    Raised when the paired Security Device is not connected.
    """


class SecurityVaultUnlockedError(SecurityVaultError):
    """
    Raised when an operation is forbidden while Vault is unlocked.
    """


class SecurityVaultService:
    """
    Hardware-independent coordinator between:

        SecurityDeviceRegistry
        PairingManager
        Vault

    The service does not implement hardware-specific operations.

    Lifecycle:

        UNPAIRED
            |
            v
        PAIRING
            |
            v
         PAIRED
            |
            | explicit credential
            v
       VAULT UNLOCKED
            |
            v
       VAULT LOCKED

    Physical device removal always forces the Vault into LOCKED state.
    """

    def __init__(
        self,
        registry: SecurityDeviceRegistry,
        pairing_manager: PairingManager,
        vault: Vault,
        device_id: str,
    ) -> None:
        self.registry = registry
        self.pairing_manager = pairing_manager
        self.vault = vault
        self.device_id = device_id

    def get_pairing_state(self) -> PairingState:
        """
        Return the current persistent pairing state.
        """

        return self.pairing_manager.get_state(
            self.device_id
        )

    def is_paired(self) -> bool:
        """
        Return True only when the device is persistently paired.
        """

        return self.pairing_manager.is_paired(
            self.device_id
        )

    def is_device_available(self) -> bool:
        """
        Return True when the paired device is currently connected.
        """

        device = self.registry.get(
            self.device_id
        )

        if device is None:
            return False

        return device.is_connected()

    def is_unlocked(self) -> bool:
        """
        Return the current Vault unlock state.
        """

        return self.vault.is_unlocked

    def begin_pairing(self):
        """
        Begin explicit pairing for the Security Device.
        """

        self._require_device_available()

        return self.pairing_manager.begin_pairing(
            self.device_id
        )

    def confirm_pairing(self):
        """
        Explicitly confirm pairing.

        Pairing alone never unlocks the Vault.
        """

        self._require_device_available()

        return self.pairing_manager.confirm_pairing(
            self.device_id
        )

    def unlock(
        self,
        credential: bytes,
    ) -> None:
        """
        Explicitly unlock the Vault.

        Requirements:

            1. Security Device is connected
            2. Security Device is paired
            3. Vault has been initialized
            4. Credential is valid
        """

        self.pairing_manager.require_bound_device(
            self.device_id
        )

        self.vault.unlock(
            credential
        )

    def lock(self) -> None:
        """
        Lock the Vault.

        Lock is intentionally idempotent.
        """

        self.vault.lock()

    def unpair(self) -> bool:
        """
        Unpair the Security Device.

        Unpairing is forbidden while the Vault is unlocked.

        Returns:
            True if a pairing record existed.
        """

        if self.vault.is_unlocked:
            raise SecurityVaultUnlockedError(
                "Security Device cannot be unpaired "
                "while Vault is unlocked"
            )

        return self.pairing_manager.unpair(
            self.device_id
        )

    def put(
        self,
        name: str,
        value,
    ) -> None:
        """
        Store protected data.

        Vault itself enforces the unlocked state.
        """

        self._require_paired()
        self._require_device_available()

        self.vault.put(
            name,
            value,
        )

    def get(
        self,
        name: str,
    ):
        """
        Read protected data.
        """

        self._require_paired()
        self._require_device_available()

        return self.vault.get(
            name
        )

    def delete(
        self,
        name: str,
    ) -> None:
        """
        Delete protected data.
        """

        self._require_paired()
        self._require_device_available()

        self.vault.delete(
            name
        )

    def contains(
        self,
        name: str,
    ) -> bool:
        """
        Check whether protected data exists.
        """

        self._require_paired()
        self._require_device_available()

        return self.vault.contains(
            name
        )

    def list_names(self) -> list[str]:
        """
        Return protected data names.
        """

        self._require_paired()
        self._require_device_available()

        return self.vault.list_names()

    def handle_device_removed(
        self,
        device_id: str,
    ) -> None:
        """
        Handle physical Security Device removal.

        If the removed device belongs to this service,
        the Vault is immediately locked.

        Pairing state remains persistent.

        This means:

            unplug
                ->
            Vault LOCKED

        while the device remains PAIRED in persistent state.
        """

        if device_id != self.device_id:
            return

        self.vault.lock()

    def _require_paired(self) -> None:
        if not self.pairing_manager.is_paired(
            self.device_id
        ):
            raise SecurityVaultNotPairedError(
                f"Security Device is not paired: "
                f"{self.device_id}"
            )

    def _require_device_available(self) -> None:
        device = self.registry.get(
            self.device_id
        )

        if device is None:
            raise SecurityVaultDeviceUnavailableError(
                f"Security Device is not connected: "
                f"{self.device_id}"
            )

        if not device.is_connected():
            raise SecurityVaultDeviceUnavailableError(
                f"Security Device is not connected: "
                f"{self.device_id}"
            )
