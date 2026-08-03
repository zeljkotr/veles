"""
veles/tts/speak.py

Offline Serbian TTS using Piper.
"""

import subprocess
import os

from veles.tts.piper_tts import synthesize_to_file


def speak(text: str) -> None:
    """
    Generate speech with Piper and play it.
    """

    wav_file = synthesize_to_file(text)

    try:
        subprocess.run(
            [
                "aplay",
                wav_file
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )

    finally:
        if os.path.exists(wav_file):
            os.remove(wav_file)