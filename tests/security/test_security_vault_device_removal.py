import os
import sys

sys.path.insert(0, "/opt/veles")

from veles.security.discovery.scanner import discover_security_devices
from veles.security.service.vault_service import (
    SecurityVaultService,
    SecurityVaultDeviceUnavailableError,
)
from veles.security.pairing.manager import PairingManager
from veles.security.runtime.registry import SecurityDeviceRegistry
from veles.security.vault.vault import Vault
from veles.security.vault import VaultLockedError


print("=" * 72)
print("SECURITY VAULT — DEVICE REMOVAL BOUNDARY TEST")
print("=" * 72)


# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

CREDENTIAL = b"veles-device-removal-boundary-test"

SECRET_NAME = "device_removal_boundary_secret"
SECRET_VALUE = "DEVICE-REMOVAL-BOUNDARY-OK"

STATE_PATH = (
    "/tmp/veles-security-vault-device-removal-boundary.json"
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

for index, candidate in enumerate(devices, start=1):
    info = candidate.get_info()

    print(
        f"DEVICE {index}: "
        f"{type(candidate).__name__} "
        f"ID={info.identity.device_id} "
        f"PROVIDER={info.identity.provider}"
    )

device = devices[0]
device_info = device.get_info()
device_id = device_info.identity.device_id

print("SELECTED:", device_id)
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
        "Security Device was not registered"
    )

print("REGISTRY: DEVICE PRESENT")

pairing_manager = PairingManager(
    registry=registry
)

if not pairing_manager.is_paired(device_id):
    pairing_manager.begin_pairing(device_id)

if not pairing_manager.is_paired(device_id):
    raise RuntimeError(
        "Security Device pairing failed"
    )

print("PAIRING: PAIRED")
print("OK")


# ---------------------------------------------------------------------------
# [2] INITIALIZE VAULT
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[2] INITIALIZE VAULT")
print("=" * 72)

vault = Vault(STATE_PATH)
vault.initialize(CREDENTIAL)

service = SecurityVaultService(
    registry=registry,
    pairing_manager=pairing_manager,
    vault=vault,
    device_id=device_id,
)

if service.is_unlocked():
    raise RuntimeError(
        "Vault unexpectedly unlocked after initialize"
    )

print("VAULT: INITIALIZED")
print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [3] UNLOCK + STORE SECRET
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[3] UNLOCK + STORE SECRET")
print("=" * 72)

service.unlock(CREDENTIAL)

if not service.is_unlocked():
    raise RuntimeError(
        "Vault failed to unlock"
    )

print("VAULT: UNLOCKED")

service.put(
    SECRET_NAME,
    SECRET_VALUE,
)

if service.get(SECRET_NAME) != SECRET_VALUE:
    raise RuntimeError(
        "Secret verification failed before removal"
    )

print("SECRET: STORED")
print("SECRET: VERIFIED")
print("OK")


# ---------------------------------------------------------------------------
# [4] DEVICE REMOVAL
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[4] DEVICE REMOVED")
print("=" * 72)

service.handle_device_removed(
    device_id
)

if service.is_unlocked():
    raise RuntimeError(
        "Vault remained unlocked after device removal"
    )

print("REMOVE EVENT: PROCESSED")
print("VAULT: LOCKED")

removed = registry.remove(
    device_id
)

if removed is None:
    raise RuntimeError(
        "Device was not present in registry during removal"
    )

print("REGISTRY: DEVICE REMOVED")
print("OK")


# ---------------------------------------------------------------------------
# [5] SECRET ACCESS AFTER REMOVE
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[5] SECRET ACCESS AFTER REMOVE")
print("=" * 72)

try:
    service.get(
        SECRET_NAME
    )
except SecurityVaultDeviceUnavailableError as exc:
    print("GET AFTER REMOVE: REJECTED")
    print("EXCEPTION:", type(exc).__name__)
else:
    raise RuntimeError(
        "GET succeeded after device removal"
    )

if service.is_unlocked():
    raise RuntimeError(
        "Vault became unlocked after rejected GET"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [6] PAIRING MUST SURVIVE REMOVAL
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[6] PAIRING PERSISTENCE")
print("=" * 72)

if service.is_paired() is not True:
    raise RuntimeError(
        "Pairing was unexpectedly removed after device removal"
    )

print("PAIRING: STILL PAIRED")
print("OK")


# ---------------------------------------------------------------------------
# [7] RECONNECT DEVICE
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[7] DEVICE RECONNECT")
print("=" * 72)

registry.add(device)

if not registry.contains(device_id):
    raise RuntimeError(
        "Device was not restored to registry"
    )

if not service.is_device_available():
    raise RuntimeError(
        "Device is not available after reconnect"
    )

print("REGISTRY: DEVICE PRESENT")
print("DEVICE: AVAILABLE")

if service.is_unlocked():
    raise RuntimeError(
        "Vault unexpectedly unlocked after reconnect"
    )

print("VAULT: STILL LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [8] RECONNECT MUST NOT AUTO-UNLOCK
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[8] NO AUTO-UNLOCK AFTER RECONNECT")
print("=" * 72)

if service.is_unlocked():
    raise RuntimeError(
        "Vault automatically unlocked after reconnect"
    )

print("VAULT: LOCKED")
print("AUTO-UNLOCK: NOT OCCURRED")
print("OK")


# ---------------------------------------------------------------------------
# [9] EXPLICIT UNLOCK AFTER RECONNECT
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[9] EXPLICIT UNLOCK AFTER RECONNECT")
print("=" * 72)

service.unlock(CREDENTIAL)

if not service.is_unlocked():
    raise RuntimeError(
        "Vault failed to unlock after reconnect"
    )

print("VAULT: UNLOCKED")

recovered = service.get(
    SECRET_NAME
)

if recovered != SECRET_VALUE:
    raise RuntimeError(
        "Secret recovery failed after reconnect"
    )

print("SECRET: RECOVERED")
print("SECRET: VERIFIED")
print("OK")


# ---------------------------------------------------------------------------
# [10] FINAL LOCK
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[10] FINAL LOCK")
print("=" * 72)

service.lock()

if service.is_unlocked():
    raise RuntimeError(
        "Vault failed to lock"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# RESULT
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("DEVICE REMOVAL BOUNDARY TEST: PASS")
print("=" * 72)
