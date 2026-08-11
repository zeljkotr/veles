#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$ROOT_DIR/assets/manifest.json"
VENV="$ROOT_DIR/venv"

echo
echo "================================"
echo "        VELES INSTALLER"
echo "================================"
echo

if [[ ! -f "$MANIFEST" ]]; then
    echo "ERROR: assets/manifest.json not found."
    exit 1
fi

for command in python3 curl tar zstd sha256sum; do
    if ! command -v "$command" >/dev/null 2>&1; then
        echo "ERROR: $command is required."
        exit 1
    fi
done

echo "[1/5] Creating Python environment..."

if [[ ! -d "$VENV" ]]; then
    python3 -m venv "$VENV"
fi

source "$VENV/bin/activate"

echo "[2/5] Installing Python dependencies..."

python -m pip install --upgrade pip
python -m pip install -r "$ROOT_DIR/requirements.txt"

echo "[3/5] Configuring PostgreSQL..."

if [[ -z "${VELES_DATABASE_URL:-}" ]]; then
    read -rp "PostgreSQL URL [postgresql+psycopg2://veles_app@localhost:5432/veles]: " DB_URL

    if [[ -z "$DB_URL" ]]; then
        DB_URL="postgresql+psycopg2://veles_app@localhost:5432/veles"
    fi

    export VELES_DATABASE_URL="$DB_URL"
    read -rsp "PostgreSQL password: " PGPASSWORD
    echo
    export PGPASSWORD
fi

python -m veles.database.init_database

echo "[4/5] Downloading VELES assets..."

ASSET_URL="$(python3 - "$MANIFEST" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    manifest = json.load(f)

print(manifest["bundle"]["url"])
PY
)"

EXPECTED_SIZE="$(python3 - "$MANIFEST" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    manifest = json.load(f)

print(manifest["bundle"]["size"])
PY
)"

EXPECTED_SHA256="$(python3 - "$MANIFEST" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    manifest = json.load(f)

print(manifest["bundle"]["sha256"])
PY
)"

TMP_DIR="$(mktemp -d)"
BUNDLE="$TMP_DIR/veles-assets.tar.zst"

cleanup() {
    rm -rf "$TMP_DIR"
}

trap cleanup EXIT

curl -fL --progress-bar "$ASSET_URL" -o "$BUNDLE"

ACTUAL_SIZE="$(stat -c '%s' "$BUNDLE")"

if [[ "$ACTUAL_SIZE" != "$EXPECTED_SIZE" ]]; then
    echo "ERROR: asset size mismatch."
    echo "Expected: $EXPECTED_SIZE"
    echo "Actual:   $ACTUAL_SIZE"
    exit 1
fi

echo "Asset size OK."

ACTUAL_SHA256="$(sha256sum "$BUNDLE" | awk '{print $1}')"

if [[ "$ACTUAL_SHA256" != "$EXPECTED_SHA256" ]]; then
    echo "ERROR: asset SHA256 mismatch."
    exit 1
fi

echo "Asset SHA256 OK."

echo "[5/5] Installing assets..."

tar -I zstd -xf "$BUNDLE" -C "$ROOT_DIR"

echo
echo "================================"
echo "      VELES INSTALL COMPLETE"
echo "================================"
echo
echo "Environment:"
echo "  $VENV"
echo
echo "Database:"
echo "  initialized"
echo
echo "Assets:"
echo "  installed and verified"
echo
