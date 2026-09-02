import os
import sys

sys.path.insert(0, "/opt/veles")

from veles.security.discovery.scanner import discover_security_devices
from veles.security.service.vault_service import (
    SecurityVaultService,
)
from veles.security.pairing.manager import PairingManager
from veles.security.runtime.registry import SecurityDeviceRegistry
from veles.security.vault.vault import Vault, VaultLockedError


print("=" * 72)
print("SECURITY VAULT — VAULT PERSISTENCE BOUNDARY TEST")
print("=" * 72)


# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

CREDENTIAL = b"veles-vault-persistence-boundary-test"

SECRET_NAME = "vault_persistence_boundary_secret"
SECRET_VALUE = "VAULT-PERSISTENCE-BOUNDARY-OK"

STATE_PATH = (
    "/tmp/veles-security-vault-persistence-boundary.json"
)


# ---------------------------------------------------------------------------
# CLEAN TEST STATE
# ---------------------------------------------------------------------------

if os.path.exists(STATE_PATH):
    os.remove(STATE_PATH)


# ---------------------------------------------------------------------------
# [0] REAL DEVICE DISCOVERY
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[0] REAL DEVICE DISCOVERY")
print("=" * 72)

devices = discover_security_devices()

print("DISCOVERED:", len(devices))

if not devices:
    raise RuntimeError(
        "No real Security Device discovered"
    )

device = devices[0]
info = device.get_info()

device_id = info.identity.device_id

print(
    "DEVICE:",
    type(device).__name__,
    "ID=",
    device_id,
    "PROVIDER=",
    info.identity.provider,
)

print("OK")


# ---------------------------------------------------------------------------
# [1] REGISTRY + PAIRING
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[1] REGISTRY + PAIRING")
print("=" * 72)

registry = SecurityDeviceRegistry()
registry.add(device)

if not registry.contains(device_id):
    raise RuntimeError(
        "Real device was not registered"
    )

print("REGISTRY: DEVICE PRESENT")

pairing_manager = PairingManager(
    registry=registry
)

if not pairing_manager.is_paired(device_id):
    pairing_manager.begin_pairing(device_id)

if not pairing_manager.is_paired(device_id):
    raise RuntimeError(
        "Device pairing failed"
    )

print("PAIRING: PAIRED")
print("OK")


# ---------------------------------------------------------------------------
# [2] FIRST VAULT INSTANCE
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[2] FIRST VAULT INSTANCE")
print("=" * 72)

vault1 = Vault(STATE_PATH)
vault1.initialize(CREDENTIAL)

if vault1.is_unlocked:
    raise RuntimeError(
        "Vault unexpectedly unlocked after initialization"
    )

print("VAULT #1: INITIALIZED")
print("VAULT #1: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [3] FIRST SERVICE — STORE SECRET
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[3] FIRST SERVICE — STORE SECRET")
print("=" * 72)

service1 = SecurityVaultService(
    registry=registry,
    pairing_manager=pairing_manager,
    vault=vault1,
    device_id=device_id,
)

if service1.is_unlocked():
    raise RuntimeError(
        "Service unexpectedly unlocked"
    )

service1.unlock(CREDENTIAL)

if not service1.is_unlocked():
    raise RuntimeError(
        "Vault failed to unlock"
    )

print("VAULT #1: UNLOCKED")

service1.put(
    SECRET_NAME,
    SECRET_VALUE,
)

if service1.get(SECRET_NAME) != SECRET_VALUE:
    raise RuntimeError(
        "Initial secret verification failed"
    )

print("SECRET: STORED")
print("SECRET: VERIFIED")


# ---------------------------------------------------------------------------
# [4] EXPLICIT LOCK BEFORE RELOAD
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[4] LOCK BEFORE RELOAD")
print("=" * 72)

service1.lock()

if service1.is_unlocked():
    raise RuntimeError(
        "Vault failed to lock"
    )

if vault1.is_unlocked:
    raise RuntimeError(
        "Vault object remains unlocked"
    )

print("SERVICE #1: LOCKED")
print("VAULT #1: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [5] NEW VAULT INSTANCE — PERSISTENCE RELOAD
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[5] NEW VAULT INSTANCE — RELOAD")
print("=" * 72)

vault2 = Vault(STATE_PATH)

if vault2.is_unlocked:
    raise RuntimeError(
        "New Vault instance unexpectedly restored UNLOCKED state"
    )

print("VAULT #2: CREATED")
print("VAULT #2: LOCKED")
print("UNLOCKED STATE: NOT PERSISTED")
print("OK")


# ---------------------------------------------------------------------------
# [6] NEW SERVICE MUST START LOCKED
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[6] NEW SERVICE — LOCKED BOUNDARY")
print("=" * 72)

service2 = SecurityVaultService(
    registry=registry,
    pairing_manager=pairing_manager,
    vault=vault2,
    device_id=device_id,
)

if service2.is_unlocked():
    raise RuntimeError(
        "New service unexpectedly reports Vault unlocked"
    )

print("SERVICE #2: CREATED")
print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [7] SECRET MUST NOT BE ACCESSIBLE WHILE LOCKED
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[7] LOCKED SECRET ACCESS")
print("=" * 72)

access_rejected = False

try:
    service2.get(SECRET_NAME)

except VaultLockedError as exc:
    access_rejected = True

    print("GET: REJECTED")
    print("EXCEPTION:", type(exc).__name__)

if not access_rejected:
    raise RuntimeError(
        "Persisted secret was accessible while Vault was locked"
    )

if not service2.is_unlocked():
    print("VAULT: STILL LOCKED")

print("OK")


# ---------------------------------------------------------------------------
# [8] EXPLICIT UNLOCK AFTER RELOAD
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[8] EXPLICIT UNLOCK AFTER RELOAD")
print("=" * 72)

service2.unlock(CREDENTIAL)

if not service2.is_unlocked():
    raise RuntimeError(
        "Explicit unlock failed after Vault reload"
    )

print("VAULT #2: UNLOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [9] SECRET RECOVERY
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[9] SECRET RECOVERY")
print("=" * 72)

recovered = service2.get(SECRET_NAME)

if recovered != SECRET_VALUE:
    raise RuntimeError(
        "Persisted secret recovery failed"
    )

print("SECRET: RECOVERED")
print("SECRET: VERIFIED")
print("OK")


# ---------------------------------------------------------------------------
# [10] LOCK AGAIN
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[10] FINAL LOCK")
print("=" * 72)

service2.lock()

if service2.is_unlocked():
    raise RuntimeError(
        "Final Vault lock failed"
    )

if vault2.is_unlocked:
    raise RuntimeError(
        "Vault object remains unlocked after final lock"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# RESULT
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("VAULT PERSISTENCE BOUNDARY TEST: PASS")
print("=" * 72)
