from __future__ import annotations

import tempfile
from pathlib import Path

from veles.security.discovery.scanner import (
    discover_security_devices,
)
from veles.security.runtime.registry import (
    SecurityDeviceRegistry,
)
from veles.security.pairing.manager import (
    PairingManager,
    PairingError,
)
from veles.security.pairing.store import (
    PairingStore,
)
from veles.security.service.vault_service import (
    SecurityVaultService,
    SecurityVaultNotPairedError,
    SecurityVaultDeviceUnavailableError,
    SecurityVaultUnlockedError,
)
from veles.security.vault.vault import Vault


print("=" * 72)
print("SECURITY DEVICE — IDENTITY ISOLATION TEST")
print("=" * 72)


# ---------------------------------------------------------------------------
# [0] REAL DEVICE DISCOVERY
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[0] REAL DEVICE DISCOVERY")
print("=" * 72)

devices = discover_security_devices()

print(f"DISCOVERED: {len(devices)}")

if not devices:
    raise RuntimeError(
        "No Security Device discovered"
    )

device = devices[0]
info = device.get_info()
identity = info.identity

print(
    "DEVICE:",
    type(device).__name__,
    "ID=",
    identity.device_id,
    "PROVIDER=",
    identity.provider,
)
print("OK")


# ---------------------------------------------------------------------------
# SETUP
# ---------------------------------------------------------------------------

with tempfile.TemporaryDirectory(
    prefix="veles-identity-isolation-"
) as temp_dir:

    temp_path = Path(temp_dir)

    registry = SecurityDeviceRegistry()

    pairing_store = PairingStore(
        path=temp_path / "pairing.json"
    )

    pairing_manager = PairingManager(
        registry=registry,
        store=pairing_store,
    )

    vault = Vault(
        temp_path / "vault.json"
    )

    service = SecurityVaultService(
        registry=registry,
        pairing_manager=pairing_manager,
        vault=vault,
        device_id=identity.device_id,
    )

    credential = b"VELes-identity-isolation-test"
    secret_name = "identity-test-secret"
    secret_value = "IDENTITY_ISOLATION_SECRET"


    # -----------------------------------------------------------------------
    # [1] REGISTER REAL DEVICE
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[1] REGISTER REAL DEVICE")
    print("=" * 72)

    added = registry.add(device)

    if not added:
        raise RuntimeError(
            "Real device was not newly registered"
        )

    if not registry.contains(identity.device_id):
        raise RuntimeError(
            "Real device is missing from registry"
        )

    if not service.is_device_available():
        raise RuntimeError(
            "Real Security Device is not available"
        )

    print("REGISTRY: DEVICE PRESENT")
    print("DEVICE: AVAILABLE")
    print("OK")


    # -----------------------------------------------------------------------
    # [2] PAIR REAL DEVICE
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[2] PAIR REAL DEVICE")
    print("=" * 72)

    service.begin_pairing()
    service.confirm_pairing()

    if not service.is_paired():
        raise RuntimeError(
            "Real device was not paired"
        )

    print("PAIRING: PAIRED")
    print("OK")


    # -----------------------------------------------------------------------
    # [3] CREATE + VERIFY VAULT
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[3] CREATE + VERIFY VAULT")
    print("=" * 72)

    vault.initialize(credential)

    if vault.is_unlocked:
        raise RuntimeError(
            "Vault remained unlocked after initialize"
        )

    service.unlock(credential)

    if not service.is_unlocked():
        raise RuntimeError(
            "Vault failed to unlock"
        )

    service.put(
        secret_name,
        secret_value,
    )

    recovered = service.get(
        secret_name
    )

    if recovered != secret_value:
        raise RuntimeError(
            "Secret verification failed"
        )

    service.lock()

    if service.is_unlocked():
        raise RuntimeError(
            "Vault failed to lock"
        )

    print("VAULT: CREATED")
    print("SECRET: VERIFIED")
    print("VAULT: LOCKED")
    print("OK")


    # -----------------------------------------------------------------------
    # [4] UNPAIR REAL DEVICE WHILE LOCKED
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[4] UNPAIR REAL DEVICE")
    print("=" * 72)

    if service.is_unlocked():
        raise RuntimeError(
            "Vault must be locked before unpair"
        )

    result = service.unpair()

    if not result:
        raise RuntimeError(
            "Expected existing pairing record"
        )

    if service.is_paired():
        raise RuntimeError(
            "Device remained paired after unpair"
        )

    print("PAIRING: UNPAIRED")
    print("VAULT: LOCKED")
    print("OK")


    # -----------------------------------------------------------------------
    # [5] ACCESS AFTER UNPAIR MUST BE REJECTED
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[5] ACCESS AFTER UNPAIR")
    print("=" * 72)

    try:
        service.get(secret_name)
    except SecurityVaultNotPairedError:
        print("GET: REJECTED")
        print(
            "EXCEPTION:",
            "SecurityVaultNotPairedError",
        )
    else:
        raise RuntimeError(
            "Unpaired device was allowed Vault access"
        )

    print("VAULT ACCESS: BLOCKED")
    print("OK")


    # -----------------------------------------------------------------------
    # [6] UNKNOWN IDENTITY MUST NOT ACCESS VAULT
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[6] UNKNOWN IDENTITY")
    print("=" * 72)

    unknown_device_id = (
        identity.device_id
        + "-unknown"
    )

    unknown_service = SecurityVaultService(
        registry=registry,
        pairing_manager=pairing_manager,
        vault=vault,
        device_id=unknown_device_id,
    )

    if unknown_service.is_paired():
        raise RuntimeError(
            "Unknown identity unexpectedly appears paired"
        )

    try:
        unknown_service.get(secret_name)
    except SecurityVaultNotPairedError:
        print("UNKNOWN IDENTITY: REJECTED")
        print(
            "EXCEPTION:",
            "SecurityVaultNotPairedError",
        )
    else:
        raise RuntimeError(
            "Unknown identity was allowed Vault access"
        )

    print("VAULT ACCESS: BLOCKED")
    print("OK")


    # -----------------------------------------------------------------------
    # [7] REPAIR REAL DEVICE
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[7] REPAIR REAL DEVICE")
    print("=" * 72)

    service.begin_pairing()
    service.confirm_pairing()

    if not service.is_paired():
        raise RuntimeError(
            "Real device failed to pair again"
        )

    print("PAIRING: PAIRED AGAIN")
    print("OK")


    # -----------------------------------------------------------------------
    # [8] RECOVER EXISTING VAULT AFTER REPAIR
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[8] RECOVER VAULT AFTER REPAIR")
    print("=" * 72)

    service.unlock(credential)

    if not service.is_unlocked():
        raise RuntimeError(
            "Vault failed to unlock after repair"
        )

    recovered = service.get(
        secret_name
    )

    if recovered != secret_value:
        raise RuntimeError(
            "Secret recovery failed after repair"
        )

    print("VAULT: UNLOCKED")
    print("SECRET: RECOVERED")
    print("SECRET: VERIFIED")
    print("OK")


    # -----------------------------------------------------------------------
    # [9] UNPAIR WHILE UNLOCKED MUST BE REJECTED
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[9] UNPAIR WHILE VAULT UNLOCKED")
    print("=" * 72)

    try:
        service.unpair()
    except SecurityVaultUnlockedError:
        print("UNPAIR: REJECTED")
        print(
            "EXCEPTION:",
            "SecurityVaultUnlockedError",
        )
    else:
        raise RuntimeError(
            "Unpair was allowed while Vault was unlocked"
        )

    if not service.is_paired():
        raise RuntimeError(
            "Pairing was removed despite rejection"
        )

    print("PAIRING: STILL PAIRED")
    print("VAULT: UNLOCKED")
    print("OK")


    # -----------------------------------------------------------------------
    # [10] FINAL LOCK + UNPAIR
    # -----------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("[10] FINAL LOCK + UNPAIR")
    print("=" * 72)

    service.lock()

    if service.is_unlocked():
        raise RuntimeError(
            "Vault failed to lock"
        )

    result = service.unpair()

    if not result:
        raise RuntimeError(
            "Final unpair failed"
        )

    if service.is_paired():
        raise RuntimeError(
            "Device remained paired after final unpair"
        )

    print("VAULT: LOCKED")
    print("PAIRING: REMOVED")
    print("OK")


print("\n" + "=" * 72)
print("SECURITY DEVICE IDENTITY ISOLATION TEST: PASS")
print("=" * 72)
