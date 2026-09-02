from __future__ import annotations

from dataclasses import dataclass
import subprocess

from ..device import (
    IdentityEvidence,
    SecurityDevice,
    SecurityDeviceIdentity,
    SecurityDeviceInfo,
    generate_device_identity,
)


def _udev_properties(device: str) -> dict[str, str]:
    result = subprocess.run(
        [
            "udevadm",
            "info",
            "--query=property",
            "--name",
            device,
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    properties: dict[str, str] = {}

    for line in result.stdout.splitlines():
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        properties[key] = value

    return properties


@dataclass(frozen=True)
class NVMeSecurityDevice(SecurityDevice):
    """
    V1 Security Device backend.

    The backend is intentionally responsible only for translating
    Linux USB/NVMe hardware information into the generic
    SecurityDevice interface.
    """

    device: str
    identity: SecurityDeviceIdentity
    transport: str = "usb"
    connected: bool = True

    def get_info(self) -> SecurityDeviceInfo:
        return SecurityDeviceInfo(
            identity=self.identity,
            transport=self.transport,
            capabilities=(
                "storage",
                "vault",
                "lock",
                "unlock",
            ),
        )

    def is_connected(self) -> bool:
        return self.connected

    def pair(self) -> None:
        raise NotImplementedError(
            "Pairing is implemented by the pairing layer"
        )

    def unpair(self) -> None:
        raise NotImplementedError(
            "Pairing is implemented by the pairing layer"
        )

    def unlock(self, credential: bytes) -> None:
        raise NotImplementedError(
            "Unlock is implemented by the cryptographic layer"
        )

    def lock(self) -> None:
        raise NotImplementedError(
            "Lock is implemented by the cryptographic layer"
        )


def create_nvme_security_device(
    device: str,
) -> NVMeSecurityDevice:
    properties = _udev_properties(device)

    if properties.get("ID_USB_TYPE") != "disk":
        raise ValueError(
            f"{device} is not a USB storage device"
        )

    if "usb-" not in properties.get("ID_PATH", ""):
        raise ValueError(
            f"{device} is not attached through USB"
        )

    storage_serial = (
        properties.get("ID_SERIAL_SHORT", "").strip()
    )

    usb_serial = (
        properties.get("ID_USB_SERIAL_SHORT", "").strip()
    )

    storage_model = (
        properties.get("ID_MODEL", "").strip()
    )

    usb_vendor_id = (
        properties.get("ID_USB_VENDOR_ID", "").strip()
    )

    usb_model_id = (
        properties.get("ID_USB_MODEL_ID", "").strip()
    )

    primary: list[tuple[str, str]] = []

    if storage_serial:
        primary.append(
            ("storage_serial", storage_serial)
        )
    elif usb_serial:
        primary.append(
            ("usb_serial", usb_serial)
        )

    secondary: list[tuple[str, str]] = []

    if usb_serial and storage_serial:
        secondary.append(
            ("usb_serial", usb_serial)
        )

    descriptive: list[tuple[str, str]] = []

    if storage_model:
        descriptive.append(
            ("storage_model", storage_model)
        )

    if usb_vendor_id:
        descriptive.append(
            ("usb_vendor_id", usb_vendor_id)
        )

    if usb_model_id:
        descriptive.append(
            ("usb_model_id", usb_model_id)
        )

    evidence = IdentityEvidence(
        source="nvme",
        primary=tuple(primary),
        secondary=tuple(secondary),
        descriptive=tuple(descriptive),
        location=(
            (
                "udev_path",
                properties.get("ID_PATH", ""),
            ),
        ),
    )

    identity = generate_device_identity(evidence)

    return NVMeSecurityDevice(
        device=device,
        identity=identity,
    )
