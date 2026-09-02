from __future__ import annotations

import tempfile
from pathlib import Path

from veles.security.vault.vault import (
    Vault,
    VaultLockedError,
)


print("=" * 72)
print("SECURITY VAULT — LOCK STATE BOUNDARY TEST")
print("=" * 72)


with tempfile.TemporaryDirectory(
    prefix="veles-vault-lock-test-"
) as temp_dir:

    vault_path = Path(temp_dir) / "vault.json"

    credential = b"VELes-lock-boundary-test-credential"
    secret_name = "test-secret"
    secret_value = "LOCK_STATE_SECRET_VERIFIED"

    vault = Vault(vault_path)


    # -----------------------------------------------------------------------
    # [1] CREATE VALID VAULT
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[1] CREATE VALID VAULT")
    print("=" * 72)

    vault.initialize(credential)

    if not vault.is_initialized:
        raise RuntimeError(
            "Vault was not initialized"
        )

    if vault.is_unlocked:
        raise RuntimeError(
            "Vault remained unlocked after initialize"
        )

    vault.unlock(credential)

    if not vault.is_unlocked:
        raise RuntimeError(
            "Vault failed to unlock after initialize"
        )

    vault.put(
        secret_name,
        secret_value,
    )

    if vault.get(secret_name) != secret_value:
        raise RuntimeError(
            "Secret verification failed"
        )

    print("VAULT: CREATED")
    print("VAULT: UNLOCKED")
    print("SECRET: VERIFIED")
    print("OK")


    # -----------------------------------------------------------------------
    # [2] LOCK VAULT
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[2] LOCK VAULT")
    print("=" * 72)

    vault.lock()

    if vault.is_unlocked:
        raise RuntimeError(
            "Vault remained unlocked after lock()"
        )

    print("VAULT: LOCKED")
    print("OK")


    # -----------------------------------------------------------------------
    # [3] GET WHILE LOCKED
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[3] GET WHILE LOCKED")
    print("=" * 72)

    try:
        vault.get(secret_name)
    except VaultLockedError:
        print("GET: REJECTED")
        print("EXCEPTION: VaultLockedError")
    else:
        raise RuntimeError(
            "Locked vault allowed get()"
        )

    print("VAULT: LOCKED")
    print("OK")


    # -----------------------------------------------------------------------
    # [4] PUT WHILE LOCKED
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[4] PUT WHILE LOCKED")
    print("=" * 72)

    try:
        vault.put(
            "blocked-write",
            "MUST_NOT_BE_STORED",
        )
    except VaultLockedError:
        print("PUT: REJECTED")
        print("EXCEPTION: VaultLockedError")
    else:
        raise RuntimeError(
            "Locked vault allowed put()"
        )

    print("VAULT: LOCKED")
    print("OK")


    # -----------------------------------------------------------------------
    # [5] DELETE WHILE LOCKED
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[5] DELETE WHILE LOCKED")
    print("=" * 72)

    try:
        vault.delete(secret_name)
    except VaultLockedError:
        print("DELETE: REJECTED")
        print("EXCEPTION: VaultLockedError")
    else:
        raise RuntimeError(
            "Locked vault allowed delete()"
        )

    print("VAULT: LOCKED")
    print("OK")


    # -----------------------------------------------------------------------
    # [6] CONTAINS WHILE LOCKED
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[6] CONTAINS WHILE LOCKED")
    print("=" * 72)

    try:
        vault.contains(secret_name)
    except VaultLockedError:
        print("CONTAINS: REJECTED")
        print("EXCEPTION: VaultLockedError")
    else:
        raise RuntimeError(
            "Locked vault allowed contains()"
        )

    print("VAULT: LOCKED")
    print("OK")


    # -----------------------------------------------------------------------
    # [7] LIST NAMES WHILE LOCKED
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[7] LIST NAMES WHILE LOCKED")
    print("=" * 72)

    try:
        vault.list_names()
    except VaultLockedError:
        print("LIST_NAMES: REJECTED")
        print("EXCEPTION: VaultLockedError")
    else:
        raise RuntimeError(
            "Locked vault allowed list_names()"
        )

    print("VAULT: LOCKED")
    print("OK")


    # -----------------------------------------------------------------------
    # [8] VERIFY LOCKED INTERNAL STATE
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[8] VERIFY LOCKED INTERNAL STATE")
    print("=" * 72)

    if vault.is_unlocked:
        raise RuntimeError(
            "Vault reports unlocked state"
        )

    if vault._key is not None:
        raise RuntimeError(
            "Vault key remained in memory after lock"
        )

    if vault._salt is not None:
        raise RuntimeError(
            "Vault salt remained in memory after lock"
        )

    if vault._data:
        raise RuntimeError(
            "Vault data remained in memory after lock"
        )

    print("UNLOCKED STATE: FALSE")
    print("KEY: CLEARED")
    print("SALT: CLEARED")
    print("DATA: CLEARED")
    print("OK")


    # -----------------------------------------------------------------------
    # [9] UNLOCK AFTER LOCK
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[9] UNLOCK AFTER LOCK")
    print("=" * 72)

    vault.unlock(credential)

    if not vault.is_unlocked:
        raise RuntimeError(
            "Vault failed to unlock"
        )

    recovered = vault.get(secret_name)

    if recovered != secret_value:
        raise RuntimeError(
            "Secret recovery failed after lock"
        )

    print("VAULT: UNLOCKED")
    print("SECRET: RECOVERED")
    print("SECRET: VERIFIED")
    print("OK")


    # -----------------------------------------------------------------------
    # [10] FINAL LOCK
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[10] FINAL LOCK")
    print("=" * 72)

    vault.lock()

    if vault.is_unlocked:
        raise RuntimeError(
            "Vault failed to lock"
        )

    if vault._key is not None:
        raise RuntimeError(
            "Key was not cleared"
        )

    if vault._salt is not None:
        raise RuntimeError(
            "Salt was not cleared"
        )

    if vault._data:
        raise RuntimeError(
            "Data was not cleared"
        )

    print("VAULT: LOCKED")
    print("SENSITIVE STATE: CLEARED")
    print("OK")


print("\n" + "=" * 72)
print("VAULT LOCK STATE BOUNDARY TEST: PASS")
print("=" * 72)
