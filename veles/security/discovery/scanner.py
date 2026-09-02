from __future__ import annotations

from pathlib import Path

from ..backends.nvme import (
    NVMeSecurityDevice,
    create_nvme_security_device,
)


def discover_security_devices() -> list[NVMeSecurityDevice]:
    """
    Discover compatible V1 Security Devices at runtime.

    No physical device identity, serial, model, VID/PID or
    device path is hardcoded.
    """

    devices: list[NVMeSecurityDevice] = []

    for block_device in sorted(Path("/sys/class/block").iterdir()):
        device_name = block_device.name

        if device_name.startswith("nvme"):
            continue

        device_path = f"/dev/{device_name}"

        try:
            device = create_nvme_security_device(
                device_path
            )
        except (OSError, ValueError):
            continue

        devices.append(device)

    return devices


# Backward-compatible discovery function.
def discover_usb_storage_devices():
    return discover_security_devices()
