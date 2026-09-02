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
print("SECURITY VAULT — FOREIGN / UNKNOWN DEVICE BOUNDARY TEST")
print("=" * 72)


# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

CREDENTIAL = b"veles-foreign-device-boundary-test"

SECRET_NAME = "foreign_device_boundary_secret"
SECRET_VALUE = "FOREIGN-DEVICE-BOUNDARY-OK"

STATE_PATH = (
    "/tmp/veles-security-vault-foreign-device-boundary.json"
)

FOREIGN_DEVICE_ID = (
    "veles-foreign-device-"
    "ffffffffffffffffffffffffffffffff"
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
real_device_id = device_info.identity.device_id

print("REAL DEVICE ID:", real_device_id)
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
        "Real Security Device was not registered"
    )

print("REGISTRY: REAL DEVICE PRESENT")

pairing_manager = PairingManager(
    registry=registry
)

if not pairing_manager.is_paired(real_device_id):
    pairing_manager.begin_pairing(real_device_id)

if not pairing_manager.is_paired(real_device_id):
    raise RuntimeError(
        "Real Security Device pairing failed"
    )

print("PAIRING: REAL DEVICE PAIRED")
print("OK")


# ---------------------------------------------------------------------------
# [2] INITIALIZE VAULT
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[2] INITIALIZE VAULT")
print("=" * 72)

vault = Vault(STATE_PATH)
vault.initialize(CREDENTIAL)

real_service = SecurityVaultService(
    registry=registry,
    pairing_manager=pairing_manager,
    vault=vault,
    device_id=real_device_id,
)

if real_service.is_unlocked():
    raise RuntimeError(
        "Vault unexpectedly unlocked after initialize"
    )

print("VAULT: INITIALIZED")
print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [3] REAL DEVICE BASELINE
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[3] REAL DEVICE BASELINE")
print("=" * 72)

real_service.unlock(CREDENTIAL)

if not real_service.is_unlocked():
    raise RuntimeError(
        "Real device failed to unlock Vault"
    )

print("REAL DEVICE: UNLOCKED")

real_service.put(
    SECRET_NAME,
    SECRET_VALUE,
)

if real_service.get(SECRET_NAME) != SECRET_VALUE:
    raise RuntimeError(
        "Real device secret verification failed"
    )

print("SECRET: STORED")
print("SECRET: VERIFIED")

real_service.lock()

if real_service.is_unlocked():
    raise RuntimeError(
        "Vault failed to lock"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [4] FOREIGN DEVICE MUST BE UNKNOWN
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[4] FOREIGN / UNKNOWN DEVICE")
print("=" * 72)

if registry.contains(FOREIGN_DEVICE_ID):
    raise RuntimeError(
        "Foreign device ID unexpectedly exists in registry"
    )

if pairing_manager.is_paired(FOREIGN_DEVICE_ID):
    raise RuntimeError(
        "Foreign device ID unexpectedly appears paired"
    )

print("REGISTRY: FOREIGN DEVICE ABSENT")
print("PAIRING: FOREIGN DEVICE NOT PAIRED")
print("OK")


# ---------------------------------------------------------------------------
# [5] CREATE FOREIGN SERVICE
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[5] FOREIGN DEVICE SERVICE")
print("=" * 72)

foreign_service = SecurityVaultService(
    registry=registry,
    pairing_manager=pairing_manager,
    vault=vault,
    device_id=FOREIGN_DEVICE_ID,
)

if foreign_service.is_unlocked():
    raise RuntimeError(
        "Foreign device service unexpectedly reports Vault unlocked"
    )

print("FOREIGN SERVICE: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [6] FOREIGN DEVICE + VALID CREDENTIAL
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[6] FOREIGN DEVICE + VALID CREDENTIAL")
print("=" * 72)

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

if foreign_service.is_unlocked():
    raise RuntimeError(
        "Foreign device service became unlocked"
    )

if vault.is_unlocked:
    raise RuntimeError(
        "Vault became unlocked after foreign-device attempt"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [7] FOREIGN DEVICE SECRET ACCESS
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[7] FOREIGN DEVICE SECRET ACCESS")
print("=" * 72)

get_rejected = False

try:
    foreign_service.get(SECRET_NAME)

except (
    SecurityVaultDeviceUnavailableError,
    SecurityVaultNotPairedError,
) as exc:
    get_rejected = True

    print("GET: REJECTED")
    print("EXCEPTION:", type(exc).__name__)

if not get_rejected:
    raise RuntimeError(
        "Foreign device accessed secret"
    )

if foreign_service.is_unlocked():
    raise RuntimeError(
        "Foreign device service became unlocked"
    )

if vault.is_unlocked:
    raise RuntimeError(
        "Vault became unlocked during foreign-device access"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [8] REAL DEVICE MUST REMAIN FUNCTIONAL
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[8] REAL DEVICE REMAINS FUNCTIONAL")
print("=" * 72)

real_service.unlock(CREDENTIAL)

if not real_service.is_unlocked():
    raise RuntimeError(
        "Real device failed to unlock after foreign-device attempts"
    )

print("REAL DEVICE: UNLOCKED")

recovered = real_service.get(SECRET_NAME)

if recovered != SECRET_VALUE:
    raise RuntimeError(
        "Real device secret recovery failed after foreign-device attempts"
    )

print("SECRET: RECOVERED")
print("SECRET: VERIFIED")

real_service.lock()

if real_service.is_unlocked():
    raise RuntimeError(
        "Vault failed to lock"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# RESULT
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("FOREIGN / UNKNOWN DEVICE BOUNDARY TEST: PASS")
print("=" * 72)
