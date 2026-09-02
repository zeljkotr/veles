from __future__ import annotations

import subprocess
import threading
from collections.abc import Callable

from ..device import SecurityDevice
from ..discovery.scanner import discover_security_devices
from .registry import SecurityDeviceRegistry


DeviceCallback = Callable[[SecurityDevice], None]
RemoveCallback = Callable[[str], None]


class SecurityDeviceMonitor:
    """
    Runtime monitor for VELES Security Devices.

    Linux-specific udev handling remains isolated here.

    The monitor is responsible for:
        - initial discovery
        - udev add events
        - udev remove events
        - runtime registry synchronization

    The registry and the rest of VELES remain hardware-independent.
    """

    def __init__(
        self,
        registry: SecurityDeviceRegistry | None = None,
        on_added: DeviceCallback | None = None,
        on_removed: RemoveCallback | None = None,
    ) -> None:
        self.registry = registry or SecurityDeviceRegistry()

        self.on_added = on_added
        self.on_removed = on_removed

        self._process: subprocess.Popen[str] | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        self._device_paths: dict[str, str] = {}
        self._paths_lock = threading.RLock()

    def start(self) -> None:
        """
        Start runtime monitoring.

        udev monitoring is started before initial discovery so that
        there is no intentional gap between discovery and hot-plug
        monitoring.
        """

        if self.is_running():
            return

        self._stop_event.clear()

        self._start_udev_monitor()

        self._initial_discovery()

        self._thread = threading.Thread(
            target=self._monitor_loop,
            name="veles-security-device-monitor",
            daemon=True,
        )

        self._thread.start()

        self._reconcile()

    def stop(self) -> None:
        """
        Stop runtime monitoring.

        Runtime registry contents are intentionally cleared because
        the registry represents currently connected devices only.
        """

        self._stop_event.set()

        process = self._process

        if process is not None:
            try:
                process.terminate()
                process.wait(timeout=2)
            except (
                ProcessLookupError,
                subprocess.TimeoutExpired,
            ):
                try:
                    process.kill()
                except ProcessLookupError:
                    pass

        thread = self._thread

        if thread is not None and thread.is_alive():
            thread.join(timeout=2)

        self._process = None
        self._thread = None

        self._clear_runtime_paths()
        self.registry.clear()

    def is_running(self) -> bool:
        process = self._process

        return (
            process is not None
            and process.poll() is None
            and self._thread is not None
            and self._thread.is_alive()
        )

    def _start_udev_monitor(self) -> None:
        self._process = subprocess.Popen(
            [
                "udevadm",
                "monitor",
                "--udev",
                "--subsystem-match=block",
                "--property",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )

    def _initial_discovery(self) -> None:
        """
        Discover devices already connected before monitor startup.
        """

        try:
            devices = discover_security_devices()
        except Exception:
            return

        for device in devices:
            self._register_device(device)

    def _reconcile(self) -> None:
        """
        Reconcile the runtime registry with the current hardware state.

        This protects against timing races between udev and discovery.
        """

        try:
            devices = discover_security_devices()
        except Exception:
            return

        discovered_ids: set[str] = set()

        for device in devices:
            info = device.get_info()
            discovered_ids.add(
                info.identity.device_id
            )

            self._register_device(device)

        registered_ids = {
            device.get_info().identity.device_id
            for device in self.registry.all()
        }

        for device_id in registered_ids - discovered_ids:
            self._remove_by_identity(device_id)

    def _monitor_loop(self) -> None:
        process = self._process

        if process is None or process.stdout is None:
            return

        event: dict[str, str] = {}

        try:
            for raw_line in process.stdout:
                if self._stop_event.is_set():
                    break

                line = raw_line.rstrip("\n")

                if not line:
                    self._handle_event(event)
                    event = {}
                    continue

                if "=" not in line:
                    continue

                key, value = line.split("=", 1)
                event[key] = value

            if event and not self._stop_event.is_set():
                self._handle_event(event)

        except (
            OSError,
            ValueError,
        ):
            return

    def _handle_event(
        self,
        event: dict[str, str],
    ) -> None:
        action = event.get("ACTION", "")
        device_path = event.get("DEVNAME", "")

        if not device_path:
            return

        if action == "add":
            self._handle_add(device_path)
            return

        if action == "remove":
            self._handle_remove(device_path)

    def _handle_add(
        self,
        device_path: str,
    ) -> None:
        """
        Re-run the real discovery pipeline.

        No hardware identity is constructed inside the monitor.
        """

        try:
            devices = discover_security_devices()
        except Exception:
            return

        for device in devices:
            backend_path = getattr(
                device,
                "device",
                "",
            )

            if backend_path != device_path:
                continue

            self._register_device(device)
            return

    def _handle_remove(
        self,
        device_path: str,
    ) -> None:
        """
        Remove the runtime device associated with a Linux path.
        """

        with self._paths_lock:
            device_id = self._device_paths.pop(
                device_path,
                None,
            )

        if device_id is None:
            return

        self._remove_by_identity(device_id)

    def _remove_by_identity(
        self,
        device_id: str,
    ) -> None:
        removed = self.registry.remove(
            device_id
        )

        if removed is not None and self.on_removed is not None:
            try:
                self.on_removed(device_id)
            except Exception:
                pass

    def _register_device(
        self,
        device: SecurityDevice,
    ) -> None:
        info = device.get_info()

        device_id = info.identity.device_id
        device_path = getattr(
            device,
            "device",
            "",
        )

        is_new = self.registry.add(device)

        if device_path:
            with self._paths_lock:
                self._device_paths[
                    device_path
                ] = device_id

        if is_new and self.on_added is not None:
            try:
                self.on_added(device)
            except Exception:
                pass

    def _clear_runtime_paths(self) -> None:
        with self._paths_lock:
            self._device_paths.clear()
