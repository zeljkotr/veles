"""
veles/logs/logger.py

Simple append-only event log for Veles - lets you see what commands it
ran (or refused to run) even when you weren't watching. Plain text,
one JSON object per line (JSON Lines format), easy to grep or parse later.
"""

import json
import datetime
from pathlib import Path

LOG_FILE = Path(__file__).parent / "veles.log"


def log_event(event_type: str, details: dict) -> None:
    entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event": event_type,
        **details,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
