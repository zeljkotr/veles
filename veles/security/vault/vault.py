from __future__ import annotations

import base64
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .crypto import (
    EncryptedPayload,
    decode,
    derive_key,
    encode,
    encrypt,
)


class VaultError(Exception):
    """Base exception for Vault errors."""


class VaultLockedError(VaultError):
    """Raised when an operation requires an unlocked vault."""


class VaultNotInitializedError(VaultError):
    """Raised when the vault has not been initialized."""


class VaultAlreadyInitializedError(VaultError):
    """Raised when initialize() is called on an existing vault."""


class VaultInvalidCredentialError(VaultError):
    """Raised when the vault credential is invalid."""


class Vault:
    """
    Hardware-independent encrypted Vault.

    The Vault stores encrypted JSON data on disk.

    Security model:
        credential
            ↓
        Argon2id
            ↓
        AES-256-GCM key
            ↓
        encrypted vault

    The derived key exists only while the vault is unlocked.
    """

    FORMAT_VERSION = 1

    def __init__(self, path: str | Path):
        self._path = Path(path)

        self._unlocked = False
        self._key: bytearray | None = None
        self._salt: bytes | None = None
        self._data: dict[str, Any] = {}

    @property
    def path(self) -> Path:
        return self._path

    @property
    def is_initialized(self) -> bool:
        return self._path.is_file()

    @property
    def is_unlocked(self) -> bool:
        return self._unlocked

    def initialize(self, credential: bytes) -> None:
        """
        Create a new encrypted vault.

        The Argon2 salt is generated once and becomes part of the
        persistent vault metadata.
        """

        if self.is_initialized:
            raise VaultAlreadyInitializedError(
                "vault is already initialized"
            )

        self._validate_credential(credential)

        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        salt = os.urandom(16)
        key = derive_key(
            credential,
            salt,
        )

        self._salt = salt
        self._key = bytearray(key)
        self._data = {}
        self._unlocked = True

        try:
            self._write_encrypted()
        finally:
            self._clear_memory()

    def unlock(self, credential: bytes) -> None:
        """
        Unlock an existing vault using its persistent Argon2 salt.
        """

        if not self.is_initialized:
            raise VaultNotInitializedError(
                "vault is not initialized"
            )

        self._validate_credential(credential)

        try:
            document = self._read_document()

            salt = document["salt"]
            nonce = document["nonce"]
            ciphertext = document["ciphertext"]

            key = derive_key(
                credential,
                salt,
            )

            plaintext = AESGCM(key).decrypt(
                nonce,
                ciphertext,
                None,
            )

            payload = json.loads(
                plaintext.decode("utf-8")
            )

            if payload.get("version") != self.FORMAT_VERSION:
                raise VaultInvalidCredentialError(
                    "unsupported vault format"
                )

            data = payload.get("data")

            if not isinstance(data, dict):
                raise VaultInvalidCredentialError(
                    "invalid vault data"
                )

        except VaultInvalidCredentialError:
            raise
        except Exception:
            raise VaultInvalidCredentialError(
                "invalid vault credential or corrupted vault"
            ) from None

        self._salt = salt
        self._key = bytearray(key)
        self._data = data
        self._unlocked = True

    def lock(self) -> None:
        """
        Lock the vault and clear sensitive material from memory.
        """

        self._clear_memory()

    def put(
        self,
        name: str,
        value: Any,
    ) -> None:
        """
        Store or replace a vault entry.
        """

        self._require_unlocked()
        self._validate_name(name)

        self._data[name] = value
        self._write_encrypted()

    def get(self, name: str) -> Any:
        """
        Return a vault entry.
        """

        self._require_unlocked()
        self._validate_name(name)

        if name not in self._data:
            raise KeyError(name)

        return self._data[name]

    def delete(self, name: str) -> None:
        """
        Delete a vault entry.
        """

        self._require_unlocked()
        self._validate_name(name)

        if name not in self._data:
            raise KeyError(name)

        del self._data[name]
        self._write_encrypted()

    def contains(self, name: str) -> bool:
        """
        Check whether a vault entry exists.
        """

        self._require_unlocked()
        self._validate_name(name)

        return name in self._data

    def list_names(self) -> list[str]:
        """
        Return the names of all vault entries.
        """

        self._require_unlocked()

        return sorted(self._data.keys())

    def _write_encrypted(self) -> None:
        """
        Encrypt current vault state and atomically persist it.

        IMPORTANT:
        The persistent Argon2 salt is preserved on every write.
        """

        self._require_unlocked()

        if self._salt is None:
            raise VaultError(
                "vault salt is not available"
            )

        if self._key is None:
            raise VaultLockedError(
                "vault is locked"
            )

        payload = {
            "version": self.FORMAT_VERSION,
            "data": self._data,
        }

        plaintext = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

        nonce = os.urandom(12)

        ciphertext = AESGCM(
            bytes(self._key)
        ).encrypt(
            nonce,
            plaintext,
            None,
        )

        document = {
            "version": self.FORMAT_VERSION,
            "salt": base64.b64encode(
                self._salt
            ).decode("ascii"),
            "nonce": base64.b64encode(
                nonce
            ).decode("ascii"),
            "ciphertext": base64.b64encode(
                ciphertext
            ).decode("ascii"),
        }

        self._atomic_write(document)

    def _read_document(self) -> dict[str, Any]:
        """
        Read and decode the persistent vault document.
        """

        with self._path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            document = json.load(handle)

        if not isinstance(document, dict):
            raise VaultError(
                "invalid vault document"
            )

        if document.get("version") != self.FORMAT_VERSION:
            raise VaultError(
                "unsupported vault format"
            )

        try:
            salt = base64.b64decode(
                document["salt"],
                validate=True,
            )

            nonce = base64.b64decode(
                document["nonce"],
                validate=True,
            )

            ciphertext = base64.b64decode(
                document["ciphertext"],
                validate=True,
            )
        except Exception:
            raise VaultError(
                "invalid vault encoding"
            ) from None

        if len(salt) != 16:
            raise VaultError(
                "invalid vault salt"
            )

        if len(nonce) != 12:
            raise VaultError(
                "invalid vault nonce"
            )

        if not ciphertext:
            raise VaultError(
                "invalid vault ciphertext"
            )

        return {
            "version": document["version"],
            "salt": salt,
            "nonce": nonce,
            "ciphertext": ciphertext,
        }

    def _atomic_write(
        self,
        document: dict[str, Any],
    ) -> None:
        """
        Atomically replace the vault file.

        The vault file is always created with owner-only permissions.
        """

        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        serialized = json.dumps(
            document,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        fd, temporary_path = tempfile.mkstemp(
            prefix=".vault-",
            dir=str(self._path.parent),
        )

        try:
            os.fchmod(fd, 0o600)

            with os.fdopen(
                fd,
                "wb",
            ) as handle:
                handle.write(serialized)
                handle.flush()
                os.fsync(handle.fileno())

            os.replace(
                temporary_path,
                self._path,
            )

        except Exception:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass

            raise

        try:
            os.chmod(
                self._path,
                0o600,
            )
        except OSError:
            pass

    def _require_unlocked(self) -> None:
        if not self._unlocked or self._key is None:
            raise VaultLockedError(
                "vault is locked"
            )

    @staticmethod
    def _validate_credential(
        credential: bytes,
    ) -> None:
        if not isinstance(
            credential,
            bytes,
        ):
            raise TypeError(
                "credential must be bytes"
            )

        if not credential:
            raise ValueError(
                "credential cannot be empty"
            )

    @staticmethod
    def _validate_name(name: str) -> None:
        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "vault entry name must be a string"
            )

        if not name:
            raise ValueError(
                "vault entry name cannot be empty"
            )

    def _clear_memory(self) -> None:
        """
        Clear sensitive in-memory state.
        """

        if self._key is not None:
            for index in range(
                len(self._key)
            ):
                self._key[index] = 0

        self._key = None
        self._salt = None
        self._data = {}
        self._unlocked = False
