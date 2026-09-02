from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .models import (
    PAIRING_STATE_VERSION,
    PairingRecord,
    PairingState,
)


class PairingStore:
    """
    Persistent storage for Security Device pairing state.

    No user-specific path is hardcoded.

    Path resolution:
        VELES_STATE_DIR
            ↓
        XDG_STATE_HOME
            ↓
        ~/.local/state
    """

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or self._default_path()

    @staticmethod
    def _default_path() -> Path:
        configured_state_dir = os.environ.get(
            "VELES_STATE_DIR",
            "",
        ).strip()

        if configured_state_dir:
            state_dir = Path(configured_state_dir)
        else:
            xdg_state_home = os.environ.get(
                "XDG_STATE_HOME",
                "",
            ).strip()

            if xdg_state_home:
                state_dir = Path(xdg_state_home)
            else:
                state_dir = (
                    Path.home()
                    / ".local"
                    / "state"
                )

            state_dir = state_dir / "veles"

        return (
            state_dir
            / "security"
            / "pairing.json"
        )

    def load(self) -> dict[str, PairingRecord]:
        """
        Load all persistent pairing records.

        Missing state is treated as an empty registry.
        """

        if not self.path.exists():
            return {}

        try:
            raw = json.loads(
                self.path.read_text(
                    encoding="utf-8"
                )
            )
        except (
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise RuntimeError(
                f"Unable to read pairing state: {self.path}"
            ) from exc

        if not isinstance(raw, dict):
            raise RuntimeError(
                "Invalid pairing state format"
            )

        version = raw.get("version")

        if version != PAIRING_STATE_VERSION:
            raise RuntimeError(
                "Unsupported pairing state version"
            )

        raw_devices = raw.get("devices", {})

        if not isinstance(raw_devices, dict):
            raise RuntimeError(
                "Invalid pairing device collection"
            )

        records: dict[str, PairingRecord] = {}

        for device_id, value in raw_devices.items():
            if not isinstance(device_id, str):
                continue

            if not isinstance(value, dict):
                continue

            try:
                record = PairingRecord(
                    device_id=device_id,
                    identity_version=int(
                        value["identity_version"]
                    ),
                    provider=str(
                        value["provider"]
                    ),
                    state=PairingState(
                        value["state"]
                    ),
                )
            except (
                KeyError,
                TypeError,
                ValueError,
            ) as exc:
                raise RuntimeError(
                    f"Invalid pairing record: {device_id}"
                ) from exc

            records[device_id] = record

        return records

    def save(
        self,
        records: dict[str, PairingRecord],
    ) -> None:
        """
        Atomically persist pairing records.
        """

        payload = {
            "version": PAIRING_STATE_VERSION,
            "devices": {
                device_id: {
                    "identity_version": (
                        record.identity_version
                    ),
                    "provider": record.provider,
                    "state": record.state.value,
                }
                for device_id, record
                in sorted(records.items())
            },
        }

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        ) + "\n"

        fd, temporary_path = tempfile.mkstemp(
            prefix=".pairing.",
            suffix=".tmp",
            dir=self.path.parent,
            text=True,
        )

        try:
            with os.fdopen(
                fd,
                "w",
                encoding="utf-8",
            ) as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())

            os.replace(
                temporary_path,
                self.path,
            )

        except Exception:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass

            raise

        try:
            directory_fd = os.open(
                self.path.parent,
                os.O_DIRECTORY,
            )

            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)

        except OSError:
            # Directory fsync is not available on every platform/filesystem.
            pass
