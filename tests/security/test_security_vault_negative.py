from __future__ import annotations

import tempfile
from pathlib import Path

from veles.security.discovery.scanner import discover_security_devices
from veles.security.runtime.registry import SecurityDeviceRegistry
from veles.security.pairing.manager import PairingManager, PairingError
from veles.security.pairing.store import PairingStore
from veles.security.service.vault_service import (
    SecurityVaultService,
    SecurityVaultDeviceUnavailableError,
    SecurityVaultUnlockedError,
)
from veles.security.vault.vault import (
    Vault,
    VaultLockedError,
    VaultInvalidCredentialError,
)


print("=" * 72)
print("SECURITY VAULT — NEGATIVE / SECURITY BOUNDARY TEST")
print("=" * 72)


# ---------------------------------------------------------------------------
# [0] REAL DEVICE DISCOVERY
# ---------------------------------------------------------------------------

print("\n[0] REAL DEVICE DISCOVERY")

devices = discover_security_devices()

print("DISCOVERED:", len(devices))

if not devices:
    raise RuntimeError(
        "No real compatible USB Security Device discovered"
    )

for index, device in enumerate(devices, start=1):
    info = device.get_info()
    print(
        f"DEVICE {index}: "
        f"{type(device).__name__} "
        f"ID={info.identity.device_id} "
        f"TRANSPORT={info.transport}"
    )

device = devices[0]
info = device.get_info()
device_id = info.identity.device_id

print("SELECTED:", device_id)


# ---------------------------------------------------------------------------
# TEST STATE
# ---------------------------------------------------------------------------

with tempfile.TemporaryDirectory(
    prefix="veles-security-negative-"
) as temporary_dir:

    state_dir = Path(temporary_dir) / "state"
    vault_path = Path(temporary_dir) / "vault.json"

    store = PairingStore(
        state_dir
        / "security"
        / "pairing.json"
    )

    registry = SecurityDeviceRegistry()
    registry.add(device)

    pairing_manager = PairingManager(
        registry=registry,
        store=store,
    )

    vault = Vault(vault_path)

    service = SecurityVaultService(
        registry=registry,
        pairing_manager=pairing_manager,
        vault=vault,
        device_id=device_id,
    )

    credential = b"REAL-NEGATIVE-TEST-CREDENTIAL"
    wrong_credential = b"WRONG-NEGATIVE-TEST-CREDENTIAL"

    secret_name = "negative_test_secret"
    secret_value = "negative-test-value"

    passed = 0
    skipped = 0

    # -----------------------------------------------------------------------
    # SETUP
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("SETUP")
    print("=" * 72)

    print("[S1] PAIRING")

    service.begin_pairing()
    service.confirm_pairing()

    if not service.is_paired():
        raise RuntimeError(
            "PAIRING FAILED"
        )

    print("PAIRING: PAIRED")
    print("OK")

    print("\n[S2] INITIALIZE VAULT")

    vault.initialize(
        credential
    )

    if not vault.is_initialized:
        raise RuntimeError(
            "Vault initialization failed"
        )

    if vault.is_unlocked:
        raise RuntimeError(
            "Vault initialization left Vault unlocked"
        )

    print("VAULT: INITIALIZED")
    print("VAULT: LOCKED")
    print("OK")

    print("\n[S2.1] UNLOCK WITH VALID CREDENTIAL")

    service.unlock(
        credential
    )

    if not service.is_unlocked():
        raise RuntimeError(
            "Valid credential failed to unlock Vault"
        )

    print("VAULT: UNLOCKED")
    print("OK")

    print("\n[S3] STORE CONTROL SECRET")

    service.put(
        secret_name,
        secret_value,
    )

    print("SECRET: STORED")
    print("OK")

    print("\n[S4] LOCK")

    service.lock()

    if service.is_unlocked():
        raise RuntimeError(
            "Vault failed to lock"
        )

    print("VAULT: LOCKED")
    print("OK")

    # -----------------------------------------------------------------------
    # [1] WRONG CREDENTIAL
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[1] WRONG CREDENTIAL")
    print("=" * 72)

    try:
        service.unlock(
            wrong_credential
        )
    except VaultInvalidCredentialError:
        print("WRONG CREDENTIAL: REJECTED")
    else:
        raise AssertionError(
            "Wrong credential was accepted"
        )

    if service.is_unlocked():
        raise AssertionError(
            "Vault became unlocked after wrong credential"
        )

    print("VAULT: LOCKED")
    print("PASS")
    passed += 1

    # -----------------------------------------------------------------------
    # [2] GET WHILE LOCKED
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[2] GET WHILE LOCKED")
    print("=" * 72)

    try:
        service.get(
            secret_name
        )
    except VaultLockedError:
        print("GET: REJECTED")
    else:
        raise AssertionError(
            "GET succeeded while Vault was locked"
        )

    if service.is_unlocked():
        raise AssertionError(
            "Vault became unlocked after locked GET"
        )

    print("VAULT: LOCKED")
    print("PASS")
    passed += 1

    # -----------------------------------------------------------------------
    # [3] PUT WHILE LOCKED
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[3] PUT WHILE LOCKED")
    print("=" * 72)

    try:
        service.put(
            "locked_put_test",
            "must-not-be-written",
        )
    except VaultLockedError:
        print("PUT: REJECTED")
    else:
        raise AssertionError(
            "PUT succeeded while Vault was locked"
        )

    if service.is_unlocked():
        raise AssertionError(
            "Vault became unlocked after locked PUT"
        )

    print("VAULT: LOCKED")
    print("PASS")
    passed += 1

    # -----------------------------------------------------------------------
    # [4] DEVICE REMOVED
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[4] DEVICE REMOVED")
    print("=" * 72)

    service.handle_device_removed(
        device_id
    )

    if service.is_unlocked():
        raise AssertionError(
            "Vault remained unlocked after device removal"
        )

    print("REMOVE EVENT: PROCESSED")
    print("VAULT: LOCKED")

    removed = registry.remove(
        device_id
    )

    if removed is None:
        raise AssertionError(
            "Device was not present in registry during removal"
        )

    print("REGISTRY: DEVICE REMOVED")

    try:
        service.get(
            secret_name
        )
    except SecurityVaultDeviceUnavailableError:
        print("GET AFTER REMOVE: REJECTED")
    else:
        raise AssertionError(
            "GET succeeded after device removal"
        )

    if service.is_paired() is not True:
        raise AssertionError(
            "Pairing was unexpectedly removed after physical removal"
        )

    print("PAIRING: STILL PAIRED")
    print("PASS")
    passed += 1

    # -----------------------------------------------------------------------
    # RESTORE DEVICE FOR REMAINING TESTS
    # -----------------------------------------------------------------------

    print("\n[S5] DEVICE RECONNECT")

    registry.add(device)

    if not service.is_device_available():
        raise RuntimeError(
            "Device did not become available after re-registration"
        )

    print("DEVICE: AVAILABLE")
    print("OK")

    # -----------------------------------------------------------------------
    # [5] UNKNOWN / SECOND DEVICE
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[5] UNKNOWN / UNPAIRED DEVICE")
    print("=" * 72)

    unknown_devices = [
        candidate
        for candidate in devices
        if candidate.get_info().identity.device_id != device_id
    ]

    if unknown_devices:
        unknown_device = unknown_devices[0]
        unknown_info = unknown_device.get_info()
        unknown_id = unknown_info.identity.device_id

        print("UNKNOWN DEVICE:", unknown_id)

        try:
            pairing_manager.begin_pairing(
                unknown_id
            )
        except PairingError:
            print("UNKNOWN PAIRING: REJECTED")
        else:
            raise AssertionError(
                "Unknown/unpaired device was unexpectedly accepted"
            )

        if service.is_paired() is not True:
            raise AssertionError(
                "Original pairing changed after unknown-device attempt"
            )

        if service.is_unlocked():
            raise AssertionError(
                "Vault became unlocked after unknown-device attempt"
            )

        print("ORIGINAL PAIRING: INTACT")
        print("VAULT: LOCKED")
        print("PASS")
        passed += 1

    else:
        print(
            "SKIP: No second physical compatible Security Device "
            "is currently connected."
        )
        print(
            "This boundary requires a second real device "
            "and is NOT simulated."
        )
        skipped += 1

    # -----------------------------------------------------------------------
    # [6] UNPAIR WHILE UNLOCKED
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[6] UNPAIR WHILE UNLOCKED")
    print("=" * 72)

    service.unlock(
        credential
    )

    if not service.is_unlocked():
        raise AssertionError(
            "Vault failed to unlock for unpair boundary test"
        )

    print("VAULT: UNLOCKED")

    pairing_before = service.is_paired()

    try:
        service.unpair()
    except SecurityVaultUnlockedError:
        print("UNPAIR WHILE UNLOCKED: REJECTED")
    else:
        raise AssertionError(
            "Unpair succeeded while Vault was unlocked"
        )

    if service.is_paired() != pairing_before:
        raise AssertionError(
            "Pairing changed after rejected unpair"
        )

    if not service.is_unlocked():
        raise AssertionError(
            "Rejected unpair unexpectedly locked Vault"
        )

    print("PAIRING: INTACT")
    print("VAULT: STILL UNLOCKED")

    service.lock()

    if service.is_unlocked():
        raise AssertionError(
            "Final explicit lock failed"
        )

    print("FINAL VAULT STATE: LOCKED")
    print("PASS")
    passed += 1

    # -----------------------------------------------------------------------
    # [7] FINAL SECURITY INVARIANT
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[7] FINAL SECURITY INVARIANT")
    print("=" * 72)

    if service.is_unlocked():
        raise AssertionError(
            "FINAL INVARIANT FAILED: Vault is unlocked"
        )

    if not service.is_paired():
        raise AssertionError(
            "FINAL INVARIANT FAILED: original pairing disappeared"
        )

    try:
        service.get(
            secret_name
        )
    except VaultLockedError:
        print("SECRET ACCESS: BLOCKED")
    else:
        raise AssertionError(
            "FINAL INVARIANT FAILED: secret accessible while locked"
        )

    print("VAULT: LOCKED")
    print("PAIRING: INTACT")
    print("SECRET ACCESS: BLOCKED")
    print("PASS")
    passed += 1

    # -----------------------------------------------------------------------
    # FINAL RESULT
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("SECURITY BOUNDARY RESULT")
    print("=" * 72)

    total = passed + skipped

    print(
        f"PASSED: {passed}"
    )
    print(
        f"SKIPPED: {skipped}"
    )
    print(
        f"TOTAL: {total}/7"
    )

    if total != 7:
        raise RuntimeError(
            f"Security boundary suite incomplete: {total}/7"
        )

    print("SECURITY BOUNDARY SUITE COMPLETE")

    if skipped == 0:
        print("7/7 SECURITY BOUNDARY TESTS PASSED")
    else:
        print(
            f"{passed}/7 SECURITY BOUNDARY TESTS PASSED "
            f"({skipped} SKIPPED)"
        )

    print("FINAL VAULT STATE: LOCKED")
    print("=" * 72)
