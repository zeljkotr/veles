import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/opt/veles")

from veles.security.discovery.scanner import discover_security_devices
from veles.security.service.vault_service import SecurityVaultService
from veles.security.pairing.manager import PairingManager
from veles.security.runtime.registry import SecurityDeviceRegistry
from veles.security.vault.vault import Vault


print("=" * 72)
print("SECURITY VAULT — CRASH / RESTART RECOVERY TEST")
print("=" * 72)


CREDENTIAL = b"veles-crash-recovery-test-credential"
SECRET_NAME = "crash_recovery_secret"
SECRET_VALUE = "REAL-CRASH-RECOVERY"


with tempfile.TemporaryDirectory(
    prefix="veles-crash-recovery-"
) as temporary_directory:

    state_path = Path(temporary_directory) / "vault.json"

    print("\n" + "=" * 72)
    print("[0] REAL DEVICE DISCOVERY")
    print("=" * 72)

    devices = discover_security_devices()

    print("DISCOVERED:", len(devices))

    if not devices:
        raise RuntimeError(
            "No real Security Device discovered"
        )

    for index, candidate in enumerate(
        devices,
        start=1,
    ):
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

    print("\n" + "=" * 72)
    print("[2] INITIALIZE VAULT")
    print("=" * 72)

    vault = Vault(state_path)
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

    print("\n" + "=" * 72)
    print("[3] UNLOCK")
    print("=" * 72)

    service.unlock(CREDENTIAL)

    if not service.is_unlocked():
        raise RuntimeError(
            "Vault failed to unlock"
        )

    print("VAULT: UNLOCKED")
    print("OK")

    print("\n" + "=" * 72)
    print("[4] STORE SECRET")
    print("=" * 72)

    service.put(
        SECRET_NAME,
        SECRET_VALUE,
    )

    print("SECRET: STORED")

    if service.get(SECRET_NAME) != SECRET_VALUE:
        raise RuntimeError(
            "Stored secret could not be read"
        )

    print("SECRET: VERIFIED")
    print("OK")

    print("\n" + "=" * 72)
    print("[5] SIMULATE PROCESS CRASH")
    print("=" * 72)

    if not service.is_unlocked():
        raise RuntimeError(
            "Vault is not unlocked before crash simulation"
        )

    print("VAULT BEFORE CRASH: UNLOCKED")

    del service
    del vault

    print("PROCESS STATE: DESTROYED")
    print("OK")

    print("\n" + "=" * 72)
    print("[6] RESTART VAULT SERVICE")
    print("=" * 72)

    vault = Vault(state_path)

    service = SecurityVaultService(
        registry=registry,
        pairing_manager=pairing_manager,
        vault=vault,
        device_id=device_id,
    )

    if service.is_unlocked():
        raise RuntimeError(
            "Vault unexpectedly unlocked after process restart"
        )

    print("VAULT AFTER RESTART: LOCKED")
    print("OK")

    print("\n" + "=" * 72)
    print("[7] RECOVER SECRET")
    print("=" * 72)

    service.unlock(CREDENTIAL)

    if not service.is_unlocked():
        raise RuntimeError(
            "Vault failed to unlock after restart"
        )

    print("VAULT: UNLOCKED AFTER RESTART")

    recovered = service.get(SECRET_NAME)

    if recovered != SECRET_VALUE:
        raise RuntimeError(
            "Secret recovery failed"
        )

    print("SECRET: RECOVERED")
    print("SECRET: VERIFIED")
    print("OK")

    print("\n" + "=" * 72)
    print("[8] FINAL LOCK")
    print("=" * 72)

    service.lock()

    if service.is_unlocked():
        raise RuntimeError(
            "Vault failed to lock"
        )

    print("VAULT: LOCKED")
    print("OK")

    print("\n" + "=" * 72)
    print("CRASH / RESTART RECOVERY TEST: PASS")
    print("=" * 72)
