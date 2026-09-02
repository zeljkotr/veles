import base64
import json
import os
import sys

sys.path.insert(0, "/opt/veles")

from veles.security.discovery.scanner import discover_security_devices
from veles.security.service.vault_service import SecurityVaultService
from veles.security.pairing.manager import PairingManager
from veles.security.runtime.registry import SecurityDeviceRegistry
from veles.security.vault.vault import (
    Vault,
    VaultInvalidCredentialError,
)


print("=" * 72)
print("SECURITY VAULT — VAULT CORRUPTION BOUNDARY TEST")
print("=" * 72)


# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

CREDENTIAL = b"veles-vault-corruption-boundary-test"

SECRET_NAME = "vault_corruption_boundary_secret"
SECRET_VALUE = "VAULT-CORRUPTION-BOUNDARY-OK"

STATE_PATH = (
    "/tmp/veles-security-vault-corruption-boundary.json"
)


# ---------------------------------------------------------------------------
# CLEAN STATE
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

pairing_manager = PairingManager(
    registry=registry
)

if not pairing_manager.is_paired(device_id):
    pairing_manager.begin_pairing(device_id)
    pairing_manager.confirm_pairing(device_id)

if not pairing_manager.is_paired(device_id):
    raise RuntimeError(
        "Device pairing failed"
    )

print("REGISTRY: DEVICE PRESENT")
print("PAIRING: PAIRED")
print("OK")


# ---------------------------------------------------------------------------
# [2] CREATE VALID VAULT
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[2] CREATE VALID VAULT")
print("=" * 72)

vault = Vault(STATE_PATH)
vault.initialize(CREDENTIAL)

service = SecurityVaultService(
    registry=registry,
    pairing_manager=pairing_manager,
    vault=vault,
    device_id=device_id,
)

service.unlock(CREDENTIAL)

if not service.is_unlocked():
    raise RuntimeError(
        "Vault failed to unlock after initialization"
    )

service.put(
    SECRET_NAME,
    SECRET_VALUE,
)

if service.get(SECRET_NAME) != SECRET_VALUE:
    raise RuntimeError(
        "Initial secret verification failed"
    )

service.lock()

if service.is_unlocked():
    raise RuntimeError(
        "Vault failed to lock"
    )

print("VAULT: CREATED")
print("VAULT: UNLOCKED")
print("SECRET: VERIFIED")
print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# [3] INVALID JSON
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[3] INVALID JSON")
print("=" * 72)

with open(
    STATE_PATH,
    "r",
    encoding="utf-8",
) as handle:
    original_text = handle.read()

with open(
    STATE_PATH,
    "w",
    encoding="utf-8",
) as handle:
    handle.write(
        '{"version":1,"salt":"BROKEN"'
    )

test_vault = Vault(STATE_PATH)

rejected = False

try:
    test_vault.unlock(CREDENTIAL)

except VaultInvalidCredentialError as exc:
    rejected = True

    print("UNLOCK: REJECTED")
    print("EXCEPTION:", type(exc).__name__)

if not rejected:
    raise RuntimeError(
        "Invalid JSON was accepted"
    )

if test_vault.is_unlocked:
    raise RuntimeError(
        "Vault became unlocked after invalid JSON"
    )

print("VAULT: LOCKED")

with open(
    STATE_PATH,
    "w",
    encoding="utf-8",
) as handle:
    handle.write(original_text)

print("OK")


# ---------------------------------------------------------------------------
# CORRUPTION TEST HELPER
# ---------------------------------------------------------------------------

def assert_corruption_rejected(label, mutate):
    print("\n" + "=" * 72)
    print(label)
    print("=" * 72)

    with open(
        STATE_PATH,
        "r",
        encoding="utf-8",
    ) as handle:
        original_text = handle.read()

    try:
        document = json.loads(original_text)

        mutate(document)

        with open(
            STATE_PATH,
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(
                document,
                handle,
            )

        test_vault = Vault(STATE_PATH)

        rejected = False

        try:
            test_vault.unlock(CREDENTIAL)

        except VaultInvalidCredentialError as exc:
            rejected = True

            print("UNLOCK: REJECTED")
            print("EXCEPTION:", type(exc).__name__)

        if not rejected:
            raise RuntimeError(
                "Corrupted vault was accepted"
            )

        if test_vault.is_unlocked:
            raise RuntimeError(
                "Vault became unlocked after corruption"
            )

        print("VAULT: LOCKED")
        print("OK")

    finally:
        with open(
            STATE_PATH,
            "w",
            encoding="utf-8",
        ) as handle:
            handle.write(original_text)


# ---------------------------------------------------------------------------
# [4] INVALID VERSION
# ---------------------------------------------------------------------------

assert_corruption_rejected(
    "[4] INVALID VAULT VERSION",
    lambda document: document.update(
        {"version": 999}
    ),
)


# ---------------------------------------------------------------------------
# [5] CORRUPTED SALT
# ---------------------------------------------------------------------------

assert_corruption_rejected(
    "[5] CORRUPTED SALT",
    lambda document: document.update(
        {
            "salt": base64.b64encode(
                b"corrupted-salt!"
            ).decode("ascii")
        }
    ),
)


# ---------------------------------------------------------------------------
# [6] CORRUPTED NONCE
# ---------------------------------------------------------------------------

assert_corruption_rejected(
    "[6] CORRUPTED NONCE",
    lambda document: document.update(
        {
            "nonce": base64.b64encode(
                b"bad"
            ).decode("ascii")
        }
    ),
)


# ---------------------------------------------------------------------------
# [7] CORRUPTED CIPHERTEXT
# ---------------------------------------------------------------------------

def corrupt_ciphertext(document):
    raw = base64.b64decode(
        document["ciphertext"]
    )

    if not raw:
        raise RuntimeError(
            "Ciphertext unexpectedly empty"
        )

    corrupted = bytearray(raw)

    corrupted[0] ^= 0xFF

    document["ciphertext"] = base64.b64encode(
        bytes(corrupted)
    ).decode("ascii")


assert_corruption_rejected(
    "[7] CORRUPTED CIPHERTEXT",
    corrupt_ciphertext,
)


# ---------------------------------------------------------------------------
# [8] VALID VAULT STILL RECOVERS AFTER TEST RESTORATION
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("[8] VALID VAULT RECOVERY")
print("=" * 72)

recovery_vault = Vault(STATE_PATH)

recovery_service = SecurityVaultService(
    registry=registry,
    pairing_manager=pairing_manager,
    vault=recovery_vault,
    device_id=device_id,
)


if recovery_service.is_unlocked():
    raise RuntimeError(
        "Vault unexpectedly unlocked before explicit unlock"
    )

recovery_service.unlock(CREDENTIAL)

if not recovery_service.is_unlocked():
    raise RuntimeError(
        "Valid vault failed to unlock"
    )

recovered = recovery_service.get(
    SECRET_NAME
)

if recovered != SECRET_VALUE:
    raise RuntimeError(
        "Secret recovery failed after corruption tests"
    )

print("VAULT: UNLOCKED")
print("SECRET: RECOVERED")
print("SECRET: VERIFIED")

recovery_service.lock()

if recovery_service.is_unlocked():
    raise RuntimeError(
        "Final Vault lock failed"
    )

print("VAULT: LOCKED")
print("OK")


# ---------------------------------------------------------------------------
# RESULT
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("VAULT CORRUPTION BOUNDARY TEST: PASS")
print("=" * 72)
