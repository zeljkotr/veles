#!/usr/bin/env python3
"""
Quick A/B test: Meta MMS-TTS Serbian checkpoint vs Piper.

Setup (inside your existing venv):
    pip install --break-system-packages transformers torch scipy

Usage:
    python3 test_mms_tts.py "Zdravo, ja sam Veles."

First run downloads the facebook/mms-tts-srp checkpoint (~150-300MB)
to the local HuggingFace cache, then every run after that is fully
offline. Output goes to test_mms.wav - compare it directly against
your existing Piper output for the same sentence.

Note: MMS-TTS models are trained per-language on their own text
corpus, and the Serbian checkpoint's training data may use Cyrillic
script rather than Latin. If the Latin input sounds garbled or the
tokenizer complains about unknown characters, try the same text
transliterated to Cyrillic (see transliterate_to_cyrillic below)
before concluding the model is bad.
"""

import sys

import scipy.io.wavfile
import torch
from transformers import AutoTokenizer, VitsModel

MODEL_NAME = "facebook/mms-tts-srp"

# Minimal Latin -> Cyrillic transliteration table, in case the
# Serbian MMS checkpoint expects Cyrillic input.
_LATIN_TO_CYRILLIC = {
    "lj": "љ", "nj": "њ", "dž": "џ",
    "a": "а", "b": "б", "v": "в", "g": "г", "d": "д", "đ": "ђ",
    "e": "е", "ž": "ж", "z": "з", "i": "и", "j": "ј", "k": "к",
    "l": "л", "m": "м", "n": "н", "o": "о", "p": "п", "r": "р",
    "s": "с", "t": "т", "ć": "ћ", "u": "у", "f": "ф", "h": "х",
    "c": "ц", "č": "ч", "š": "ш",
}


def transliterate_to_cyrillic(text: str) -> str:
    lowered = text.lower()
    for latin, cyr in sorted(_LATIN_TO_CYRILLIC.items(), key=lambda x: -len(x[0])):
        lowered = lowered.replace(latin, cyr)
    return lowered


def synthesize(text: str, output_path: str) -> None:
    print(f"Loading {MODEL_NAME} (first run downloads the checkpoint)...")
    model = VitsModel.from_pretrained(MODEL_NAME)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    inputs = tokenizer(text, return_tensors="pt")

    print(f"Generating speech for: {text!r}")
    with torch.no_grad():
        output = model(**inputs).waveform

    scipy.io.wavfile.write(
        output_path,
        rate=model.config.sampling_rate,
        data=output.squeeze().cpu().numpy(),
    )
    print(f"Saved to {output_path} (sample rate: {model.config.sampling_rate} Hz)")


if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else "Zdravo, ja sam Veles."

    synthesize(text, "test_mms_latin.wav")
    synthesize(transliterate_to_cyrillic(text), "test_mms_cyrillic.wav")

    print("\nDone. Compare test_mms_latin.wav and test_mms_cyrillic.wav")
    print("against your existing Piper test.wav for the same sentence.")
