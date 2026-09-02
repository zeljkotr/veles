import os
import sys

sys.path.insert(0, "/opt/veles")

from veles.security.discovery.scanner import discover_security_devices
from veles.security.service.vault_service import (
    SecurityVaultService,
    SecurityVaultDeviceUnavailableError,
    SecurityVaultNotPairedError,
)
from veles.security.pairing.manager import PairingManager
from veles.security.runtime.registry import SecurityDeviceRegistry
from veles.security.vault.vault import Vault


print("=" * 72)
print("SECURITY VAULT — SECURITY STATE COMBINATION TEST")
print("=" * 72)


# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

CREDENTIAL = b"veles-security-state-combination-test"

SECRET_NAME = "security_state_combination_secret"
SECRET_VALUE = "SECURITY-STATE-COMBINATION-OK"

STATE_PATH = (
    "/tmp/veles-security-vault-state-combinations.json"
)

FOREIGN_DEVICE_ID = (
    "veles-foreign-state-device-"
    "ffffffffffffffffffffffff"
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

real_device_id = info.identity.device_id

print(
    "DEVICE:",
    type(device).__name__,
    "ID=",
    real_device_id,
    "PROVIDER=",
    info.identity.provider,
)

print("FOREIGN DEVICE ID:", FOREIGN_DEVICE_ID)

if real_device_id == FOREIGN_DEVICE_ID:
    raise RuntimeError(
        "Foreign device ID unexpectedly matches real device ID"
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

if not registry.contains(real_device_id):
    raise RuntimeError(
        "Real device was not added to registry"
    )

print("REGISTRY: REAL DEVICE PRESENT")

pairing_manager = PairingManager(
    registry=registry
)

if not pairing_manager.is_paired(real_device_id):
    pairing_manager.begin_pairing(real_device_id)

if not pairing_manager.is_paired(real_device_id):
    raise RuntimeError(
        "Real device pairing failed"
    )

print("PAIRING: REAL DEVICE PAIRED")
print("OK")


# ---------------------------------------------------------------------------
# [2] VAULT + SERVICE
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[2] INITIALIZE VAULT + SERVICE")
print("=" * 72)

vault = Vault(STATE_PATH)
vault.initialize(CREDENTIAL)

service = SecurityVaultService(
    registry=registry,
    pairing_manager=pairing_manager,
    vault=vault,
    device_id=real_device_id,
)

if service.is_unlocked():
    raise RuntimeError(
        "Vault unexpectedly unlocked after initialization"
    )

print("VAULT: LOCKED")
print("SERVICE: CREATED")
print("OK")


# ---------------------------------------------------------------------------
# [3] PRESENT + PAIRED + LOCKED
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[3] PRESENT + PAIRED + LOCKED")
print("=" * 72)

if not service.is_device_available():
    raise RuntimeError(
        "Real device should be available"
    )

if service.is_paired() is not True:
    raise RuntimeError(
        "Real device should be paired"
    )

if service.is_unlocked():
    raise RuntimeError(
        "Vault should be locked"
    )

print("DEVICE: PRESENT")
print("PAIRING: PAIRED")
print("VAULT: LOCKED")

service.unlock(CREDENTIAL)

if not service.is_unlocked():
    raise RuntimeError(
        "Valid PRESENT + PAIRED device failed to unlock"
    )

print("VALID COMBINATION: UNLOCK ALLOWED")

service.lock()

if service.is_unlocked():
    raise RuntimeError(
        "Vault failed to lock"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [4] PRESENT + PAIRED + UNLOCKED
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[4] PRESENT + PAIRED + UNLOCKED")
print("=" * 72)

service.unlock(CREDENTIAL)

if not service.is_device_available():
    raise RuntimeError(
        "Device should remain available while unlocked"
    )

if service.is_paired() is not True:
    raise RuntimeError(
        "Device should remain paired while unlocked"
    )

if not service.is_unlocked():
    raise RuntimeError(
        "Vault should be unlocked"
    )

print("DEVICE: PRESENT")
print("PAIRING: PAIRED")
print("VAULT: UNLOCKED")

service.put(
    SECRET_NAME,
    SECRET_VALUE,
)

if service.get(SECRET_NAME) != SECRET_VALUE:
    raise RuntimeError(
        "Secret access failed in valid unlocked state"
    )

print("SECRET: ACCESSIBLE")
print("SECRET: VERIFIED")

service.lock()

if service.is_unlocked():
    raise RuntimeError(
        "Vault failed to lock"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [5] PRESENT + UNPAIRED + LOCKED
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[5] PRESENT + UNPAIRED + LOCKED")
print("=" * 72)

if service.is_unlocked():
    raise RuntimeError(
        "Vault should be locked before unpairing"
    )

removed_pairing = service.unpair()

if not removed_pairing:
    raise RuntimeError(
        "Device unpair operation failed"
    )

if not service.is_device_available():
    raise RuntimeError(
        "Device should remain present after unpair"
    )

if service.is_paired() is not False:
    raise RuntimeError(
        "Device should be unpaired"
    )

print("DEVICE: PRESENT")
print("PAIRING: UNPAIRED")
print("VAULT: LOCKED")

unlock_rejected = False

try:
    service.unlock(CREDENTIAL)

except (
    SecurityVaultDeviceUnavailableError,
    SecurityVaultNotPairedError,
) as exc:
    unlock_rejected = True

    print("UNLOCK: REJECTED")
    print("EXCEPTION:", type(exc).__name__)

if not unlock_rejected:
    raise RuntimeError(
        "Unpaired device was able to unlock Vault"
    )

if service.is_unlocked():
    raise RuntimeError(
        "Vault became unlocked while device was unpaired"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [6] PRESENT + UNPAIRED + SECRET ACCESS
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[6] PRESENT + UNPAIRED + SECRET ACCESS")
print("=" * 72)

get_rejected = False

try:
    service.get(SECRET_NAME)

except (
    SecurityVaultDeviceUnavailableError,
    SecurityVaultNotPairedError,
) as exc:
    get_rejected = True

    print("GET: REJECTED")
    print("EXCEPTION:", type(exc).__name__)

if not get_rejected:
    raise RuntimeError(
        "Unpaired device accessed secret"
    )

if service.is_unlocked():
    raise RuntimeError(
        "Vault became unlocked during unpaired access"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [7] PRESENT + PAIRING + LOCKED
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[7] PRESENT + PAIRING + LOCKED")
print("=" * 72)

record = pairing_manager.begin_pairing(real_device_id)

if not pairing_manager.is_pairing(real_device_id):
    raise RuntimeError(
        "Device did not enter PAIRING state"
    )

if pairing_manager.is_paired(real_device_id):
    raise RuntimeError(
        "Device incorrectly reports PAIRED during PAIRING"
    )

if service.is_unlocked():
    raise RuntimeError(
        "Vault should remain locked during PAIRING"
    )

print("DEVICE: PRESENT")
print("PAIRING: PAIRING")
print("VAULT: LOCKED")

unlock_rejected = False

try:
    service.unlock(CREDENTIAL)

except (
    SecurityVaultDeviceUnavailableError,
    SecurityVaultNotPairedError,
) as exc:
    unlock_rejected = True

    print("UNLOCK: REJECTED")
    print("EXCEPTION:", type(exc).__name__)

if not unlock_rejected:
    raise RuntimeError(
        "Device in PAIRING state was able to unlock Vault"
    )

if service.is_unlocked():
    raise RuntimeError(
        "Vault became unlocked during PAIRING state"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [8] REPAIR + MUST REMAIN LOCKED
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[8] REPAIR + EXPLICIT UNLOCK BOUNDARY")
print("=" * 72)

pairing_manager.confirm_pairing(real_device_id)

if not pairing_manager.is_paired(real_device_id):
    raise RuntimeError(
        "Device failed to return to PAIRED state"
    )

if service.is_unlocked():
    raise RuntimeError(
        "Pairing confirmation unexpectedly unlocked Vault"
    )

print("PAIRING: PAIRED")
print("VAULT: STILL LOCKED")

service.unlock(CREDENTIAL)

if not service.is_unlocked():
    raise RuntimeError(
        "Explicit unlock failed after repair"
    )

print("EXPLICIT UNLOCK: SUCCESS")

if service.get(SECRET_NAME) != SECRET_VALUE:
    raise RuntimeError(
        "Secret recovery failed after repair"
    )

print("SECRET: RECOVERED")
print("SECRET: VERIFIED")

service.lock()

if service.is_unlocked():
    raise RuntimeError(
        "Vault failed to lock"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [9] REMOVED + PAIRED + LOCKED
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[9] REMOVED + PAIRED + LOCKED")
print("=" * 72)

if not pairing_manager.is_paired(real_device_id):
    raise RuntimeError(
        "Device should be paired before removal test"
    )

if service.is_unlocked():
    raise RuntimeError(
        "Vault should be locked before removal"
    )

service.handle_device_removed(real_device_id)

if service.is_unlocked():
    raise RuntimeError(
        "Vault failed to lock after device removal"
    )

print("DEVICE EVENT: REMOVED")
print("VAULT: LOCKED")

removed = registry.remove(real_device_id)

if not removed:
    raise RuntimeError(
        "Registry failed to remove real device"
    )

if registry.contains(real_device_id):
    raise RuntimeError(
        "Removed device still exists in registry"
    )

if service.is_device_available():
    raise RuntimeError(
        "Removed device still reports available"
    )

if service.is_paired() is not True:
    raise RuntimeError(
        "Pairing should remain persistent after removal"
    )

print("DEVICE: ABSENT")
print("PAIRING: STILL PAIRED")
print("VAULT: LOCKED")

unlock_rejected = False

try:
    service.unlock(CREDENTIAL)

except SecurityVaultDeviceUnavailableError as exc:
    unlock_rejected = True

    print("UNLOCK: REJECTED")
    print("EXCEPTION:", type(exc).__name__)

if not unlock_rejected:
    raise RuntimeError(
        "Removed device was able to unlock Vault"
    )

if service.is_unlocked():
    raise RuntimeError(
        "Vault became unlocked while device was absent"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [10] FOREIGN + UNPAIRED + LOCKED
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[10] FOREIGN + UNPAIRED + LOCKED")
print("=" * 72)

foreign_service = SecurityVaultService(
    registry=registry,
    pairing_manager=pairing_manager,
    vault=vault,
    device_id=FOREIGN_DEVICE_ID,
)

if registry.contains(FOREIGN_DEVICE_ID):
    raise RuntimeError(
        "Foreign device unexpectedly exists in registry"
    )

if pairing_manager.is_paired(FOREIGN_DEVICE_ID):
    raise RuntimeError(
        "Foreign device unexpectedly appears paired"
    )

if foreign_service.is_unlocked():
    raise RuntimeError(
        "Foreign service should be locked"
    )

print("DEVICE: FOREIGN / UNKNOWN")
print("REGISTRY: ABSENT")
print("PAIRING: UNPAIRED")
print("VAULT: LOCKED")

unlock_rejected = False

try:
    foreign_service.unlock(CREDENTIAL)

except (
    SecurityVaultDeviceUnavailableError,
    SecurityVaultNotPairedError,
) as exc:
    unlock_rejected = True

    print("UNLOCK: REJECTED")
    print("EXCEPTION:", type(exc).__name__)

if not unlock_rejected:
    raise RuntimeError(
        "Foreign device was able to unlock Vault"
    )

if vault.is_unlocked:
    raise RuntimeError(
        "Vault became unlocked after foreign-device attempt"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [11] RECONNECT REAL DEVICE + VALID STATE RECOVERY
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[11] RECONNECT + VALID STATE RECOVERY")
print("=" * 72)

registry.add(device)

if not registry.contains(real_device_id):
    raise RuntimeError(
        "Real device failed to reconnect"
    )

if not service.is_device_available():
    raise RuntimeError(
        "Service did not detect reconnected device"
    )

if service.is_paired() is not True:
    raise RuntimeError(
        "Pairing was lost across removal/reconnect"
    )

if service.is_unlocked():
    raise RuntimeError(
        "Reconnect unexpectedly auto-unlocked Vault"
    )

print("DEVICE: PRESENT")
print("PAIRING: PAIRED")
print("VAULT: LOCKED")
print("AUTO-UNLOCK: NO")

service.unlock(CREDENTIAL)

if not service.is_unlocked():
    raise RuntimeError(
        "Explicit unlock failed after reconnect"
    )

if service.get(SECRET_NAME) != SECRET_VALUE:
    raise RuntimeError(
        "Secret recovery failed after reconnect"
    )

print("EXPLICIT UNLOCK: SUCCESS")
print("SECRET: RECOVERED")
print("SECRET: VERIFIED")

service.lock()

if service.is_unlocked():
    raise RuntimeError(
        "Final Vault lock failed"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# RESULT
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("SECURITY STATE COMBINATION TEST: PASS")
print("=" * 72)
