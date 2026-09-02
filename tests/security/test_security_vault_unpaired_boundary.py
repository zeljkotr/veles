from pathlib import Path

from veles.security.discovery.scanner import discover_security_devices
from veles.security.service.vault_service import (
    SecurityVaultService,
    SecurityVaultNotPairedError,
)
from veles.security.pairing.manager import PairingManager
from veles.security.runtime.registry import SecurityDeviceRegistry
from veles.security.vault.vault import Vault


print("=" * 72)
print("SECURITY VAULT — UNPAIRED DEVICE BOUNDARY TEST")
print("=" * 72)


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

CREDENTIAL = b"veles-unpaired-boundary-test-credential"
SECRET_NAME = "unpaired_boundary_secret"
SECRET_VALUE = "UNPAIRED-BOUNDARY-SECRET"

VAULT_PATH = Path(
    "/tmp/veles_unpaired_boundary_vault.json"
)


# ---------------------------------------------------------------------------
# CLEAN TEST STATE
# ---------------------------------------------------------------------------

if VAULT_PATH.exists():
    VAULT_PATH.unlink()


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
        "No compatible Security Device discovered"
    )

for index, candidate in enumerate(devices, start=1):
    info = candidate.get_info()

    print(
        f"DEVICE {index}: "
        f"{candidate.__class__.__name__} "
        f"ID={info.identity.device_id} "
        f"PROVIDER={info.identity.provider}"
    )

device = devices[0]
device_info = device.get_info()
device_id = device_info.identity.device_id

print("SELECTED:", device_id)
print("OK")


# ---------------------------------------------------------------------------
# [1] REGISTRY + PAIRING MANAGER
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[1] REGISTRY + PAIRING MANAGER")
print("=" * 72)

registry = SecurityDeviceRegistry()
registry.add(device)

print("REGISTRY: DEVICE PRESENT")

pairing_manager = PairingManager(registry)

if not pairing_manager.is_paired(device_id):
    raise RuntimeError(
        "Expected real device to be paired before boundary test"
    )

print("PAIRING: PAIRED")
print("OK")


# ---------------------------------------------------------------------------
# [2] INITIALIZE VAULT
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[2] INITIALIZE VAULT")
print("=" * 72)

vault = Vault(VAULT_PATH)

vault.initialize(CREDENTIAL)

print("VAULT: INITIALIZED")

vault.lock()

if vault.is_unlocked:
    raise RuntimeError(
        "Vault failed to lock"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [3] CREATE SERVICE
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[3] CREATE VAULT SERVICE")
print("=" * 72)

service = SecurityVaultService(
    registry=registry,
    pairing_manager=pairing_manager,
    vault=vault,
    device_id=device_id,
)

if service.is_unlocked():
    raise RuntimeError(
        "Vault unexpectedly unlocked"
    )

print("SERVICE: CREATED")
print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [4] UNLOCK + STORE SECRET
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[4] UNLOCK + STORE SECRET")
print("=" * 72)

service.unlock(CREDENTIAL)

if not service.is_unlocked():
    raise RuntimeError(
        "Initial Vault unlock failed"
    )

print("VAULT: UNLOCKED")

service.put(
    SECRET_NAME,
    SECRET_VALUE,
)

print("SECRET: STORED")

if service.get(SECRET_NAME) != SECRET_VALUE:
    raise RuntimeError(
        "Initial secret verification failed"
    )

print("SECRET: VERIFIED")

service.lock()

if service.is_unlocked():
    raise RuntimeError(
        "Vault failed to lock"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [5] UNPAIR DEVICE
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[5] UNPAIR DEVICE")
print("=" * 72)

removed = service.unpair()

if not removed:
    raise RuntimeError(
        "Expected existing pairing record to be removed"
    )

if pairing_manager.is_paired(device_id):
    raise RuntimeError(
        "Device is still paired after unpair"
    )

print("PAIRING: REMOVED")
print("DEVICE: STILL PRESENT")
print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [6] VALID CREDENTIAL MUST NOT UNLOCK UNPAIRED DEVICE
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[6] UNPAIRED DEVICE + VALID CREDENTIAL")
print("=" * 72)

try:
    service.unlock(CREDENTIAL)
except SecurityVaultNotPairedError:
    print("UNLOCK: REJECTED")
    print("EXCEPTION: SecurityVaultNotPairedError")
else:
    raise RuntimeError(
        "SECURITY FAILURE: valid credential unlocked "
        "Vault while device was unpaired"
    )

if service.is_unlocked():
    raise RuntimeError(
        "Vault became unlocked after rejected unpaired access"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [7] SECRET ACCESS MUST ALSO BE REJECTED
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[7] SECRET ACCESS WHILE UNPAIRED")
print("=" * 72)

try:
    service.get(SECRET_NAME)
except SecurityVaultNotPairedError:
    print("GET: REJECTED")
    print("EXCEPTION: SecurityVaultNotPairedError")
else:
    raise RuntimeError(
        "SECURITY FAILURE: secret accessible while device unpaired"
    )

if service.is_unlocked():
    raise RuntimeError(
        "Vault unexpectedly unlocked"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [8] BEGIN PAIRING
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[8] BEGIN PAIRING")
print("=" * 72)

record = pairing_manager.begin_pairing(device_id)

print(
    "PAIRING STATE:",
    record.state.value
)

if not pairing_manager.is_pairing(device_id):
    raise RuntimeError(
        "Device did not enter PAIRING state"
    )

if pairing_manager.is_paired(device_id):
    raise RuntimeError(
        "Device incorrectly became PAIRED during begin_pairing"
    )

print("PAIRING: PAIRING")
print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [9] CONFIRM PAIRING
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[9] CONFIRM PAIRING")
print("=" * 72)

record = pairing_manager.confirm_pairing(device_id)

print(
    "PAIRING STATE:",
    record.state.value
)

if not pairing_manager.is_paired(device_id):
    raise RuntimeError(
        "Device did not become PAIRED after confirmation"
    )

print("PAIRING: PAIRED")

if service.is_unlocked():
    raise RuntimeError(
        "Pairing confirmation automatically unlocked Vault"
    )

print("VAULT: STILL LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [10] EXPLICIT UNLOCK AFTER REPAIRING
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[10] EXPLICIT UNLOCK AFTER REPAIRING")
print("=" * 72)

service.unlock(CREDENTIAL)

if not service.is_unlocked():
    raise RuntimeError(
        "Explicit unlock after re-pairing failed"
    )

print("VAULT: UNLOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [11] SECRET RECOVERY
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[11] SECRET RECOVERY")
print("=" * 72)

recovered = service.get(SECRET_NAME)

if recovered != SECRET_VALUE:
    raise RuntimeError(
        "Secret recovery failed"
    )

print("SECRET: RECOVERED")
print("SECRET: VERIFIED")
print("OK")


# ---------------------------------------------------------------------------
# [12] FINAL LOCK
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[12] FINAL LOCK")
print("=" * 72)

service.lock()

if service.is_unlocked():
    raise RuntimeError(
        "Vault failed final lock"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# RESULT
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("UNPAIRED DEVICE BOUNDARY TEST: PASS")
print("=" * 72)
