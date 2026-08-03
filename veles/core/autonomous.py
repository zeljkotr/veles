"""
veles/core/autonomous.py

Runs an unattended system check - no chat, no user waiting for a
response. Used by the systemd timer (see scripts/veles_autonomous_check.py)
to let Veles notice problems on its own and speak up about them, instead
of only reacting when asked.

Deliberately does NOT route the notification message through the LLM -
a fixed, reliable phrasing matters more here than natural language
variety, since this is the path that's supposed to catch real problems
while you're not watching. An unreliable LLM-generated alert message
would defeat the purpose.
"""

import json
import subprocess
from pathlib import Path

from ..tools.system import system_info
from ..logs.logger import log_event

WATCHLIST_FILE = Path(__file__).parent.parent / "config" / "watchlist.json"

_DEFAULT_WATCHLIST = {
    "cpu_threshold": 90,
    "ram_threshold": 90,
    "disk_threshold": 90,
    "systemd_services": [],
    "docker_containers": [],
}


def _load_watchlist():
    if not WATCHLIST_FILE.exists():
        return dict(_DEFAULT_WATCHLIST)
    try:
        with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = dict(_DEFAULT_WATCHLIST)
        merged.update(data)
        return merged
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULT_WATCHLIST)


def _check_systemd_service(name):
    try:
        result = subprocess.run(
            ["systemctl", "is-active", name],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5
        )
        return result.stdout.strip() == "active"
    except Exception:
        return False


def _check_docker_container(name):
    try:
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Status}}", name],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5
        )
        return result.returncode == 0 and result.stdout.strip() == "running"
    except Exception:
        return False


def run_autonomous_check():
    """
    Returns a list of issue strings (empty list = everything fine).
    Also logs the check - and any issues found - via logs/logger.py.
    """
    watchlist = _load_watchlist()
    info = system_info()
    issues = []

    cpu_percent = float(info["cpu_usage"].rstrip("%"))
    if cpu_percent >= watchlist["cpu_threshold"]:
        issues.append(f"CPU opterećenje je {cpu_percent}% (prag {watchlist['cpu_threshold']}%)")

    ram_percent = float(info["memory_percent"].rstrip("%"))
    if ram_percent >= watchlist["ram_threshold"]:
        issues.append(f"Memorija je na {ram_percent}% (prag {watchlist['ram_threshold']}%)")

    try:
        disk_total = float(info["disk_total"].split()[0])
        disk_free = float(info["disk_free"].split()[0])
        disk_used_percent = round((1 - disk_free / disk_total) * 100, 1) if disk_total else 0
        if disk_used_percent >= watchlist["disk_threshold"]:
            issues.append(f"Disk je popunjen {disk_used_percent}% (prag {watchlist['disk_threshold']}%)")
    except (ValueError, ZeroDivisionError, IndexError):
        pass

    for service in watchlist["systemd_services"]:
        if not _check_systemd_service(service):
            issues.append(f"Servis '{service}' nije aktivan")

    for container in watchlist["docker_containers"]:
        if not _check_docker_container(container):
            issues.append(f"Docker container '{container}' ne radi")

    log_event("autonomous_check", {"issues_found": len(issues), "details": issues})

    return issues
