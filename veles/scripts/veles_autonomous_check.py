#!/usr/bin/env python3
"""
scripts/veles_autonomous_check.py

Standalone entry point for the veles-checks systemd timer. Runs one
unattended check cycle; if anything looks wrong, speaks it out loud
and prints it - otherwise stays silent (no need to announce "sve je
u redu" every 15 minutes).
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from veles.core.autonomous import run_autonomous_check
from veles.tts.speak import speak

if __name__ == "__main__":
    issues = run_autonomous_check()

    if not issues:
        print("[veles-autonomous] Sve je u redu, nema upozorenja.")
    else:
        message = "Veles javlja: " + "; ".join(issues)
        print(f"[veles-autonomous] {message}")
        try:
            speak(message)
        except Exception as e:
            print(f"[veles-autonomous] Glasovni izlaz nije uspeo: {e}")
