"""
veles/tools/command_tool.py

Executes a shell command that the planner extracted from a natural-
language request (e.g. "restartuj nginx" -> "systemctl restart nginx").

Every attempt - whether run or refused - is logged via veles/logs/logger.py.
Commands matching an obviously destructive pattern are refused rather
than silently executed. A proper interactive confirmation flow (e.g. via
the web interface, with a confirm button) can be layered on top of this
later - for now, refused commands must be run manually if you're sure.
"""

import subprocess

from ..logs.logger import log_event


DESTRUCTIVE_PATTERNS = [
    "rm -rf",
    "mkfs",
    " dd if=",
    "shutdown",
    "reboot",
    ":(){ :|:& };:",
    "chmod -r 777",
    "> /dev/sd",
    "fdisk",
    "drop database",
    "drop table",
]


def _looks_destructive(command: str):
    lowered = command.lower()
    for pattern in DESTRUCTIVE_PATTERNS:
        if pattern in lowered:
            return pattern
    return None


def run_command(context):
    plan = context.get("plan", {})
    question = context.get("question", "")
    command = (plan.get("command") or "").strip()

    if not command:
        return {
            "executed": False,
            "command": "",
            "output": "Nisam uspeo da prepoznam konkretnu komandu iz zahteva.",
        }

    risky_pattern = _looks_destructive(command)

    if risky_pattern:
        log_event("command_refused", {
            "question": question,
            "command": command,
            "reason": f"matched destructive pattern: {risky_pattern}",
        })
        return {
            "executed": False,
            "command": command,
            "output": f"Ova komanda deluje rizično (sadrži '{risky_pattern}') - "
                      f"nisam je izvršio. Pokreni je ručno u terminalu ako si siguran.",
        }

    log_event("command_started", {"question": question, "command": command})

    try:
        result = subprocess.run(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=30
        )
        output = result.stdout.strip() or result.stderr.strip() or "(bez izlaza)"
        success = result.returncode == 0

        log_event("command_finished", {
            "question": question,
            "command": command,
            "returncode": result.returncode,
            "success": success,
        })

        return {"executed": True, "command": command, "output": output, "success": success}

    except subprocess.TimeoutExpired:
        log_event("command_timeout", {"question": question, "command": command})
        return {"executed": False, "command": command, "output": "Komanda je istekla (timeout 30s)."}
    except Exception as e:
        log_event("command_error", {"question": question, "command": command, "error": str(e)})
        return {"executed": False, "command": command, "output": f"Greška: {e}"}
