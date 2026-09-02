from __future__ import annotations

from threading import RLock

from ..device import SecurityDevice


class SecurityDeviceRegistry:
    """
    Runtime registry of currently connected VELES Security Devices.

    The registry is hardware-independent.
    It stores generic SecurityDevice instances only.
    """

    def __init__(self) -> None:
        self._devices: dict[str, SecurityDevice] = {}
        self._lock = RLock()

    def add(self, device: SecurityDevice) -> bool:
        """
        Add or replace a device.

        Returns:
            True  if a new device was added.
            False if the device identity was already registered.
        """

        info = device.get_info()
        device_id = info.identity.device_id

        with self._lock:
            if device_id in self._devices:
                self._devices[device_id] = device
                return False

            self._devices[device_id] = device
            return True

    def remove(self, device_id: str) -> SecurityDevice | None:
        """
        Remove a device by VELES device identity.
        """

        with self._lock:
            return self._devices.pop(device_id, None)

    def get(self, device_id: str) -> SecurityDevice | None:
        """
        Return a registered device by identity.
        """

        with self._lock:
            return self._devices.get(device_id)

    def all(self) -> list[SecurityDevice]:
        """
        Return a snapshot of all currently registered devices.
        """

        with self._lock:
            return list(self._devices.values())

    def contains(self, device_id: str) -> bool:
        """
        Check whether a device identity is currently registered.
        """

        with self._lock:
            return device_id in self._devices

    def clear(self) -> None:
        """
        Remove all runtime devices.
        """

        with self._lock:
            self._devices.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._devices)
