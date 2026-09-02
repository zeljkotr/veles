from __future__ import annotations

import base64
import os
from dataclasses import dataclass

from argon2.low_level import Type, hash_secret_raw
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32

ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 64 * 1024
ARGON2_PARALLELISM = 2


@dataclass(frozen=True)
class EncryptedPayload:
    salt: bytes
    nonce: bytes
    ciphertext: bytes


def derive_key(
    credential: bytes,
    salt: bytes,
) -> bytes:
    if not isinstance(credential, bytes):
        raise TypeError("credential must be bytes")

    if not credential:
        raise ValueError("credential must not be empty")

    if len(salt) != SALT_SIZE:
        raise ValueError("invalid salt length")

    return hash_secret_raw(
        secret=credential,
        salt=salt,
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_PARALLELISM,
        hash_len=KEY_SIZE,
        type=Type.ID,
    )


def encrypt(
    plaintext: bytes,
    credential: bytes,
) -> EncryptedPayload:
    if not isinstance(plaintext, bytes):
        raise TypeError("plaintext must be bytes")

    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)

    key = derive_key(credential, salt)

    ciphertext = AESGCM(key).encrypt(
        nonce,
        plaintext,
        None,
    )

    return EncryptedPayload(
        salt=salt,
        nonce=nonce,
        ciphertext=ciphertext,
    )


def decrypt(
    payload: EncryptedPayload,
    credential: bytes,
) -> bytes:
    key = derive_key(
        credential,
        payload.salt,
    )

    return AESGCM(key).decrypt(
        payload.nonce,
        payload.ciphertext,
        None,
    )


def encode(payload: EncryptedPayload) -> dict[str, str]:
    return {
        "salt": base64.b64encode(payload.salt).decode("ascii"),
        "nonce": base64.b64encode(payload.nonce).decode("ascii"),
        "ciphertext": base64.b64encode(payload.ciphertext).decode("ascii"),
    }


def decode(data: dict[str, str]) -> EncryptedPayload:
    return EncryptedPayload(
        salt=base64.b64decode(data["salt"]),
        nonce=base64.b64decode(data["nonce"]),
        ciphertext=base64.b64decode(data["ciphertext"]),
    )
