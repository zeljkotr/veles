"""
VELES Security Checks

Read-only local security inspection.

The module never changes system configuration.
"""

import os
import pwd
import socket
import subprocess
from pathlib import Path


def _run(command, timeout=5):
    """
    Execute a local command safely.
    """

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        return {
            "available": True,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip()
        }

    except FileNotFoundError:

        return {
            "available": False,
            "returncode": None,
            "stdout": "",
            "stderr": "command not found"
        }

    except Exception as e:

        return {
            "available": False,
            "returncode": None,
            "stdout": "",
            "stderr": str(e)
        }


def check_users():
    """
    Inspect local system users.
    """

    users = []

    try:

        for entry in pwd.getpwall():

            users.append(
                {
                    "username": entry.pw_name,
                    "uid": entry.pw_uid,
                    "gid": entry.pw_gid,
                    "home": entry.pw_dir,
                    "shell": entry.pw_shell
                }
            )

        return {
            "status": "healthy",
            "message": f"Found {len(users)} local users",
            "data": users
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e),
            "data": []
        }


def check_privileged_users():
    """
    Find users with UID 0.
    """

    privileged = []

    try:

        for entry in pwd.getpwall():

            if entry.pw_uid == 0:

                privileged.append(
                    entry.pw_name
                )

        return {
            "status": "healthy",
            "message": (
                f"Found {len(privileged)} UID 0 users"
            ),
            "data": privileged
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e),
            "data": []
        }


def check_listening_ports():
    """
    Inspect listening TCP/UDP sockets.

    Uses ss when available.
    """

    result = _run(
        [
            "ss",
            "-lntup"
        ]
    )

    if not result["available"]:

        return {
            "status": "error",
            "message": result["stderr"],
            "data": []
        }

    if result["returncode"] != 0:

        return {
            "status": "error",
            "message": result["stderr"],
            "data": []
        }

    lines = result["stdout"].splitlines()

    return {
        "status": "healthy",
        "message": (
            f"Found {max(len(lines) - 1, 0)} "
            "listening sockets"
        ),
        "data": lines
    }


def check_services():
    """
    Inspect running system services.

    Uses systemctl when available.
    """

    result = _run(
        [
            "systemctl",
            "list-units",
            "--type=service",
            "--state=running",
            "--no-pager",
            "--no-legend"
        ]
    )

    if not result["available"]:

        return {
            "status": "error",
            "message": result["stderr"],
            "data": []
        }

    if result["returncode"] != 0:

        return {
            "status": "error",
            "message": result["stderr"],
            "data": []
        }

    lines = result["stdout"].splitlines()

    return {
        "status": "healthy",
        "message": f"Found {len(lines)} running services",
        "data": lines
    }


def check_ssh():
    """
    Inspect SSH service/configuration.
    """

    ssh_service = _run(
        [
            "systemctl",
            "is-active",
            "ssh"
        ]
    )

    if ssh_service["available"]:

        active = (
            ssh_service["returncode"] == 0
            and ssh_service["stdout"] == "active"
        )

        return {
            "status": (
                "healthy"
                if active
                else "warning"
            ),
            "message": (
                "SSH service is active"
                if active
                else "SSH service is not active"
            ),
            "data": ssh_service["stdout"]
        }

    config_paths = [
        Path("/etc/ssh/sshd_config"),
        Path("/etc/sshd_config")
    ]

    existing = [
        str(path)
        for path in config_paths
        if path.exists()
    ]

    if existing:

        return {
            "status": "warning",
            "message": "SSH configuration detected",
            "data": existing
        }

    return {
        "status": "warning",
        "message": (
            "SSH service/configuration not detected"
        ),
        "data": []
    }


def check_firewall():
    """
    Detect available firewall and inspect status.

    Read-only.
    """

    checks = []

    ufw = _run(
        [
            "ufw",
            "status"
        ]
    )

    if ufw["available"]:

        checks.append(
            {
                "name": "ufw",
                "available": True,
                "status": (
                    ufw["stdout"]
                    if ufw["returncode"] == 0
                    else ufw["stderr"]
                ),
                "returncode": ufw["returncode"]
            }
        )

    firewall_cmd = _run(
        [
            "firewall-cmd",
            "--state"
        ]
    )

    if firewall_cmd["available"]:

        checks.append(
            {
                "name": "firewalld",
                "available": True,
                "status": (
                    firewall_cmd["stdout"]
                    if firewall_cmd["returncode"] == 0
                    else firewall_cmd["stderr"]
                ),
                "returncode": firewall_cmd["returncode"]
            }
        )

    nft = _run(
        [
            "nft",
            "list",
            "ruleset"
        ]
    )

    if nft["available"]:

        checks.append(
            {
                "name": "nftables",
                "available": True,
                "status": (
                    "ruleset available"
                    if nft["returncode"] == 0
                    else nft["stderr"]
                ),
                "returncode": nft["returncode"]
            }
        )

    if not checks:

        return {
            "status": "warning",
            "message": (
                "No supported firewall tool detected"
            ),
            "data": []
        }

    active = any(
        (
            check["returncode"] == 0
            and (
                check["status"] == "active"
                or check["status"] == "running"
                or check["status"] == "ruleset available"
                or check["status"] == "Status: active"
            )
        )
        for check in checks
    )

    return {
        "status": (
            "healthy"
            if active
            else "warning"
        ),
        "message": (
            f"Detected {len(checks)} firewall interface(s)"
        ),
        "data": checks
    }


def check_system():
    """
    Basic local system security context.
    """

    try:

        uid = os.getuid()

        user = pwd.getpwuid(
            uid
        ).pw_name

        return {
            "status": "healthy",
            "message": (
                f"System inspection completed "
                f"for user {user}"
            ),
            "data": {
                "hostname": socket.gethostname(),
                "uid": uid,
                "user": user
            }
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e),
            "data": {}
        }