import os
import sys

sys.path.insert(0, "/opt/veles")

from veles.security.discovery.scanner import discover_security_devices
from veles.security.service.vault_service import SecurityVaultService
from veles.security.pairing.manager import PairingManager
from veles.security.runtime.registry import SecurityDeviceRegistry
from veles.security.vault.vault import Vault


print("=" * 72)
print("SECURITY VAULT — CREDENTIAL FAILURE BOUNDARY TEST")
print("=" * 72)


# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

CREDENTIAL = b"veles-credential-boundary-test"
WRONG_CREDENTIAL = b"WRONG-CREDENTIAL"

SECRET_NAME = "credential_boundary_secret"
SECRET_VALUE = "CREDENTIAL-BOUNDARY-OK"

STATE_PATH = "/tmp/veles-security-vault-credential-boundary.json"


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
    pairing_manager.confirm_pairing(device_id)

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
# [3] VALID UNLOCK + STORE SECRET
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[3] VALID UNLOCK + STORE SECRET")
print("=" * 72)

service.unlock(CREDENTIAL)

if not service.is_unlocked():
    raise RuntimeError(
        "Vault failed to unlock with valid credential"
    )

print("VAULT: UNLOCKED")

service.put(
    SECRET_NAME,
    SECRET_VALUE,
)

if service.get(SECRET_NAME) != SECRET_VALUE:
    raise RuntimeError(
        "Stored secret could not be verified"
    )

print("SECRET: STORED")
print("SECRET: VERIFIED")
print("OK")


# ---------------------------------------------------------------------------
# [4] LOCK BEFORE INVALID CREDENTIAL TEST
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[4] LOCK BEFORE INVALID CREDENTIAL TEST")
print("=" * 72)

service.lock()

if service.is_unlocked():
    raise RuntimeError(
        "Vault failed to lock"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [5] WRONG CREDENTIAL MUST BE REJECTED
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[5] WRONG CREDENTIAL")
print("=" * 72)

wrong_credential_rejected = False

try:
    service.unlock(WRONG_CREDENTIAL)
except Exception as exc:
    wrong_credential_rejected = True
    print("UNLOCK: REJECTED")
    print("EXCEPTION:", type(exc).__name__)

if not wrong_credential_rejected:
    raise RuntimeError(
        "Wrong credential was accepted"
    )

print("OK")


# ---------------------------------------------------------------------------
# [6] VAULT MUST REMAIN LOCKED
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[6] VERIFY LOCKED STATE")
print("=" * 72)

if service.is_unlocked():
    raise RuntimeError(
        "Vault became unlocked after invalid credential"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [7] SECRET MUST NOT BE ACCESSIBLE
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[7] SECRET ACCESS WHILE LOCKED")
print("=" * 72)

secret_access_denied = False

try:
    service.get(SECRET_NAME)
except Exception as exc:
    secret_access_denied = True
    print("SECRET: ACCESS DENIED")
    print("EXCEPTION:", type(exc).__name__)

if not secret_access_denied:
    raise RuntimeError(
        "Secret was accessible while Vault was locked"
    )

print("OK")


# ---------------------------------------------------------------------------
# [8] VALID CREDENTIAL AFTER FAILURE
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[8] VALID CREDENTIAL AFTER FAILURE")
print("=" * 72)

service.unlock(CREDENTIAL)

if not service.is_unlocked():
    raise RuntimeError(
        "Valid credential failed after invalid credential attempt"
    )

print("VAULT: UNLOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [9] SECRET MUST STILL BE VALID
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[9] SECRET INTEGRITY")
print("=" * 72)

recovered = service.get(SECRET_NAME)

if recovered != SECRET_VALUE:
    raise RuntimeError(
        "Secret changed after invalid credential attempt"
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
print("CREDENTIAL FAILURE BOUNDARY TEST: PASS")
print("=" * 72)
