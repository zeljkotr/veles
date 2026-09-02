from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from .identity import SecurityDeviceIdentity


@dataclass(frozen=True)
class SecurityDeviceInfo:
    """
    Hardware-independent description of a VELES Security Device.
    """

    identity: SecurityDeviceIdentity
    transport: str
    capabilities: tuple[str, ...]


class SecurityDevice(ABC):
    """
    Generic VELES Security Device interface.

    Hardware-specific implementations must remain behind this API.
    """

    @abstractmethod
    def get_info(self) -> SecurityDeviceInfo:
        raise NotImplementedError

    @abstractmethod
    def is_connected(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def pair(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def unpair(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def unlock(self, credential: bytes) -> None:
        raise NotImplementedError

    @abstractmethod
    def lock(self) -> None:
        raise NotImplementedError
