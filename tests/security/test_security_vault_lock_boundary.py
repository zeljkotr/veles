from pathlib import Path

from veles.security.discovery.scanner import discover_security_devices
from veles.security.service.vault_service import SecurityVaultService
from veles.security.pairing.manager import PairingManager
from veles.security.runtime.registry import SecurityDeviceRegistry
from veles.security.vault.vault import Vault, VaultLockedError


print("=" * 72)
print("SECURITY VAULT — LOCK BOUNDARY TEST")
print("=" * 72)


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

CREDENTIAL = b"veles-lock-boundary-test-credential"
SECRET_NAME = "lock_boundary_secret"
SECRET_VALUE = "LOCK-BOUNDARY-SECRET"

VAULT_PATH = Path(
    "/tmp/veles_lock_boundary_vault.json"
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
# [1] REGISTRY + PAIRING
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[1] REGISTRY + PAIRING")
print("=" * 72)

registry = SecurityDeviceRegistry()
registry.add(device)

print("REGISTRY: DEVICE PRESENT")

pairing_manager = PairingManager(registry)

if pairing_manager.is_paired(device_id):
    print("PAIRING: ALREADY PAIRED")
else:
    pairing_manager.begin_pairing(device_id)
    print("PAIRING: PAIRED")

if not pairing_manager.is_paired(device_id):
    raise RuntimeError(
        "Device pairing failed"
    )

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
# [4] EXPLICIT UNLOCK
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[4] EXPLICIT UNLOCK")
print("=" * 72)

service.unlock(CREDENTIAL)

if not service.is_unlocked():
    raise RuntimeError(
        "Vault unlock failed"
    )

print("VAULT: UNLOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [5] STORE + VERIFY SECRET
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[5] STORE + VERIFY SECRET")
print("=" * 72)

service.put(
    SECRET_NAME,
    SECRET_VALUE,
)

print("SECRET: STORED")

recovered = service.get(
    SECRET_NAME
)

if recovered != SECRET_VALUE:
    raise RuntimeError(
        "Initial secret verification failed"
    )

print("SECRET: VERIFIED")
print("OK")


# ---------------------------------------------------------------------------
# [6] LOCK
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[6] LOCK VAULT")
print("=" * 72)

service.lock()

if service.is_unlocked():
    raise RuntimeError(
        "Vault failed to lock"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [7] SECRET ACCESS AFTER LOCK
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[7] SECRET ACCESS AFTER LOCK")
print("=" * 72)

try:
    service.get(
        SECRET_NAME
    )
except VaultLockedError:
    print("GET AFTER LOCK: REJECTED")
    print("EXCEPTION: VaultLockedError")
else:
    raise RuntimeError(
        "SECURITY FAILURE: secret accessible after Vault lock"
    )

if service.is_unlocked():
    raise RuntimeError(
        "Vault unexpectedly unlocked after rejected access"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [8] RE-UNLOCK
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[8] EXPLICIT RE-UNLOCK")
print("=" * 72)

service.unlock(CREDENTIAL)

if not service.is_unlocked():
    raise RuntimeError(
        "Vault re-unlock failed"
    )

print("VAULT: UNLOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [9] SECRET RECOVERY
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[9] SECRET RECOVERY AFTER RE-UNLOCK")
print("=" * 72)

recovered = service.get(
    SECRET_NAME
)

if recovered != SECRET_VALUE:
    raise RuntimeError(
        "Secret recovery failed after re-unlock"
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
        "Vault failed final lock"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# RESULT
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("VAULT LOCK BOUNDARY TEST: PASS")
print("=" * 72)
