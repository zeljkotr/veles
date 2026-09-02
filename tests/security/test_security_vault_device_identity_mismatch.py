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


print("=" * 72)
print("SECURITY VAULT — DEVICE IDENTITY MISMATCH BOUNDARY TEST")
print("=" * 72)


# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

CREDENTIAL = b"veles-device-identity-boundary-test"

SECRET_NAME = "device_identity_boundary_secret"
SECRET_VALUE = "DEVICE-IDENTITY-BOUNDARY-OK"

STATE_PATH = "/tmp/veles-security-vault-device-identity-boundary.json"

FAKE_DEVICE_ID = (
    "veles-fake-device-"
    "000000000000000000000000000000000000"
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
print("FAKE DEVICE ID:", FAKE_DEVICE_ID)

if real_device_id == FAKE_DEVICE_ID:
    raise RuntimeError(
        "Test fake device ID unexpectedly matches real device ID"
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
# [2] INITIALIZE REAL VAULT
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[2] INITIALIZE REAL VAULT")
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
# [3] REAL DEVICE ACCESS
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[3] REAL DEVICE ACCESS")
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
        "Secret verification failed"
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
# [4] FORGED / UNKNOWN DEVICE IDENTITY
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[4] FORGED DEVICE IDENTITY")
print("=" * 72)

if registry.contains(FAKE_DEVICE_ID):
    raise RuntimeError(
        "Fake device ID unexpectedly exists in registry"
    )

if pairing_manager.is_paired(FAKE_DEVICE_ID):
    raise RuntimeError(
        "Fake device ID unexpectedly appears paired"
    )

print("REGISTRY: FAKE DEVICE ABSENT")
print("PAIRING: FAKE DEVICE NOT PAIRED")
print("OK")


# ---------------------------------------------------------------------------
# [5] SERVICE CREATED WITH WRONG DEVICE ID
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[5] SERVICE WITH WRONG DEVICE ID")
print("=" * 72)

fake_service = SecurityVaultService(
    registry=registry,
    pairing_manager=pairing_manager,
    vault=vault,
    device_id=FAKE_DEVICE_ID,
)

if fake_service.is_unlocked():
    raise RuntimeError(
        "Fake-identity service unexpectedly reports Vault unlocked"
    )

print("FAKE SERVICE: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [6] WRONG DEVICE ID MUST NOT UNLOCK
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[6] WRONG DEVICE ID UNLOCK ATTEMPT")
print("=" * 72)

unlock_rejected = False

try:
    fake_service.unlock(CREDENTIAL)
except SecurityVaultDeviceUnavailableError as exc:
    unlock_rejected = True

    print("UNLOCK: REJECTED")
    print("EXCEPTION:", type(exc).__name__)

if not unlock_rejected:
    raise RuntimeError(
        "Wrong device identity was not rejected"
    )

print("OK")


# ---------------------------------------------------------------------------
# [7] VAULT MUST REMAIN LOCKED
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[7] VERIFY VAULT REMAINS LOCKED")
print("=" * 72)

if vault.is_unlocked:
    raise RuntimeError(
        "Vault became unlocked after wrong device identity attempt"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [8] WRONG DEVICE ID MUST NOT READ SECRET
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[8] SECRET ACCESS THROUGH WRONG DEVICE ID")
print("=" * 72)

secret_rejected = False

try:
    fake_service.get(SECRET_NAME)
except Exception as exc:
    secret_rejected = True

    print("SECRET: ACCESS DENIED")
    print("EXCEPTION:", type(exc).__name__)

if not secret_rejected:
    raise RuntimeError(
        "Secret was accessible through wrong device identity"
    )

print("OK")


# ---------------------------------------------------------------------------
# [9] REAL DEVICE IDENTITY STILL WORKS
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[9] REAL DEVICE IDENTITY AFTER ATTACK")
print("=" * 72)

real_service.unlock(CREDENTIAL)

if not real_service.is_unlocked():
    raise RuntimeError(
        "Real device failed to unlock after identity mismatch attempt"
    )

print("REAL DEVICE: UNLOCKED")

if real_service.get(SECRET_NAME) != SECRET_VALUE:
    raise RuntimeError(
        "Secret was corrupted after identity mismatch attempt"
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
print("DEVICE IDENTITY MISMATCH BOUNDARY TEST: PASS")
print("=" * 72)
