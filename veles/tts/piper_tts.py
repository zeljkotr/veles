"""
veles/tts/piper_tts.py

Generates a WAV file from text using Piper (offline neural TTS) with the
Serbian voice model - much better and more consistent quality than the
browser's built-in speechSynthesis, which tends to slip between Serbian
and English mid-sentence depending on which system voice it picks.

Install:
    pip install piper-tts

Download the Serbian voice model once, before first use:
    cd ~/veles
    mkdir -p models
    python3 -m piper.download_voices --data-dir models sr_RS-serbski_institut-medium
"""

import subprocess
import tempfile
import os
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent.parent
PIPER_MODEL_PATH = _PROJECT_ROOT / "models" / "sr_RS-serbski_institut-medium.onnx"


def synthesize_to_file(text: str) -> str:
    """
    Generates a WAV file for the given text and returns its path.
    Caller is responsible for moving/cleaning up the file afterwards.
    """
    if not PIPER_MODEL_PATH.exists():
        raise RuntimeError(
            f"Piper voice model not found at {PIPER_MODEL_PATH}. Download it with: "
            f"python3 -m piper.download_voices --data-dir models sr_RS-serbski_institut-medium"
        )

    fd, output_path = tempfile.mkstemp(suffix=".wav", prefix="veles_tts_")
    os.close(fd)

    process = subprocess.run(
        ["piper", "--model", str(PIPER_MODEL_PATH), "--output_file", output_path],
        input=text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )

    if process.returncode != 0:
        raise RuntimeError(f"Piper TTS failed: {process.stderr}")

    return output_path
