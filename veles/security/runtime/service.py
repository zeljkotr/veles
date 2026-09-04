from __future__ import annotations

import os
from pathlib import Path

from ..pairing.manager import PairingManager
from ..runtime.monitor import SecurityDeviceMonitor
from ..runtime.registry import SecurityDeviceRegistry
from ..service.vault_service import SecurityVaultService
from ..vault.vault import Vault
from .session_lock import security_session_lock


class SecurityDeviceRuntime:
    """
    Live Security Device runtime.

    Owns the runtime registry and hot-plug monitor.
    Persistent pairing remains authoritative through PairingManager.
    """

    def __init__(self) -> None:
        self.registry = SecurityDeviceRegistry()

        self.pairing_manager = PairingManager(
            registry=self.registry
        )

        self._vault_services: dict[
            str,
            SecurityVaultService,
        ] = {}

        self.monitor = SecurityDeviceMonitor(
            registry=self.registry,
            on_added=self._on_device_added,
            on_removed=self._on_device_removed,
        )

        self._started = False

    @property
    def started(self) -> bool:
        return self._started

    def start(self) -> None:
        if self._started:
            return

        self.monitor.start()
        self._started = True

        print(
            "[SECURITY DEVICE] Runtime monitor started"
        )

        self._report_state()

    def stop(self) -> None:
        if not self._started:
            return

        self.monitor.stop()
        self._started = False

        print(
            "[SECURITY DEVICE] Runtime monitor stopped"
        )

    def get_vault_service(
        self,
        device_id: str,
    ) -> SecurityVaultService:
        service = self._vault_services.get(device_id)

        if service is not None:
            return service

        vault = Vault(
            self._vault_path(device_id)
        )

        service = SecurityVaultService(
            registry=self.registry,
            pairing_manager=self.pairing_manager,
            vault=vault,
            device_id=device_id,
        )

        self._vault_services[device_id] = service

        return service

    def _on_device_added(self, device) -> None:
        info = device.get_info()
        device_id = info.identity.device_id

        print(
            "[SECURITY DEVICE] Added:",
            device_id,
            "path=",
            getattr(device, "device", ""),
        )

        if self.pairing_manager.is_paired(device_id):
            print(
                "[SECURITY DEVICE] Paired device reconnected:",
                device_id,
            )

            security_session_lock.unlock()

            print(
                "[SECURITY DEVICE] Session unlocked:",
                device_id,
            )

    def _on_device_removed(
        self,
        device_id: str,
    ) -> None:
        print(
            "[SECURITY DEVICE] Removed:",
            device_id,
        )

        service = self._vault_services.get(device_id)

        if service is not None:
            service.handle_device_removed(
                device_id
            )

            print(
                "[SECURITY DEVICE] Vault locked:",
                device_id,
            )

        security_session_lock.lock(
            "SECURITY DEVICE REQUIRED"
        )

    def _report_state(self) -> None:
        devices = self.registry.all()

        print(
            "[SECURITY DEVICE] Connected:",
            len(devices),
        )

        for device in devices:
            info = device.get_info()
            device_id = info.identity.device_id

            print(
                "[SECURITY DEVICE]",
                device_id,
                "paired=",
                self.pairing_manager.is_paired(
                    device_id
                ),
                "path=",
                getattr(device, "device", ""),
            )

    @staticmethod
    def _vault_path(
        device_id: str,
    ) -> Path:
        state_dir = os.environ.get(
            "VELES_STATE_DIR",
            "",
        ).strip()

        if state_dir:
            root = Path(state_dir)
        else:
            xdg_state_home = os.environ.get(
                "XDG_STATE_HOME",
                "",
            ).strip()

            if xdg_state_home:
                root = Path(xdg_state_home) / "veles"
            else:
                root = (
                    Path.home()
                    / ".local"
                    / "state"
                    / "veles"
                )

        return (
            root
            / "security"
            / "vault"
            / f"{device_id}.json"
        )


security_device_runtime = SecurityDeviceRuntime()
