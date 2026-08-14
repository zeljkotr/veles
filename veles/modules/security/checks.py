"""
VELES Security Checks

Read-only local security inspection.

The module never changes system configuration.
"""

import grp
import os
import platform
import pwd
import socket
import stat
import subprocess
from pathlib import Path


# ============================================================
# COMMAND EXECUTION
# ============================================================

def _run(command, timeout=5):
    """Execute a local command safely."""

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        return {
            "available": True,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }

    except FileNotFoundError:
        return {
            "available": False,
            "returncode": None,
            "stdout": "",
            "stderr": "command not found",
        }

    except subprocess.TimeoutExpired:
        return {
            "available": False,
            "returncode": None,
            "stdout": "",
            "stderr": "command timed out",
        }

    except Exception as exc:
        return {
            "available": False,
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
        }


# ============================================================
# USERS
# ============================================================

def check_users():
    """Inspect local system users."""

    users = []

    try:
        for entry in pwd.getpwall():
            users.append(
                {
                    "username": entry.pw_name,
                    "uid": entry.pw_uid,
                    "gid": entry.pw_gid,
                    "home": entry.pw_dir,
                    "shell": entry.pw_shell,
                }
            )

        return {
            "status": "healthy",
            "message": f"Found {len(users)} local users",
            "data": users,
        }

    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "data": [],
        }


# ============================================================
# PRIVILEGED USERS
# ============================================================

def check_privileged_users():
    """Find users with UID 0."""

    privileged = []

    try:
        for entry in pwd.getpwall():
            if entry.pw_uid == 0:
                privileged.append(entry.pw_name)

        return {
            "status": "healthy",
            "message": (
                f"Found {len(privileged)} UID 0 users"
            ),
            "data": privileged,
        }

    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "data": [],
        }


# ============================================================
# LISTENING PORTS
# ============================================================

def check_listening_ports():
    """Inspect listening TCP/UDP sockets."""

    result = _run(
        ["ss", "-lntup"]
    )

    if not result["available"]:
        return {
            "status": "error",
            "message": result["stderr"],
            "data": [],
        }

    if result["returncode"] != 0:
        return {
            "status": "error",
            "message": (
                result["stderr"]
                or "Unable to inspect listening sockets"
            ),
            "data": [],
        }

    lines = result["stdout"].splitlines()

    return {
        "status": "healthy",
        "message": (
            f"Found {max(len(lines) - 1, 0)} "
            "listening sockets"
        ),
        "data": lines,
    }


# ============================================================
# SERVICES
# ============================================================

def check_services():
    """Inspect running system services."""

    result = _run(
        [
            "systemctl",
            "list-units",
            "--type=service",
            "--state=running",
            "--no-pager",
            "--no-legend",
        ]
    )

    if not result["available"]:
        return {
            "status": "error",
            "message": result["stderr"],
            "data": [],
        }

    if result["returncode"] != 0:
        return {
            "status": "error",
            "message": (
                result["stderr"]
                or "Unable to inspect running services"
            ),
            "data": [],
        }

    lines = [
        line
        for line in result["stdout"].splitlines()
        if line.strip()
    ]

    return {
        "status": "healthy",
        "message": (
            f"Found {len(lines)} running services"
        ),
        "data": lines,
    }


# ============================================================
# SSH
# ============================================================

def check_ssh():
    """Inspect SSH service and configuration."""

    for service_name in ("ssh", "sshd"):

        result = _run(
            [
                "systemctl",
                "is-active",
                service_name,
            ]
        )

        if not result["available"]:
            continue

        state = result["stdout"].strip()

        if (
            result["returncode"] == 0
            and state == "active"
        ):
            return {
                "status": "healthy",
                "message": "SSH service is active",
                "data": {
                    "service": service_name,
                    "state": "active",
                    "port": 22,
                    "configuration": (
                        "read-only inspection"
                    ),
                },
            }

        if state == "inactive":
            return {
                "status": "warning",
                "message": "SSH service is not active",
                "data": {
                    "service": service_name,
                    "state": "inactive",
                    "port": 22,
                    "configuration": (
                        "read-only inspection"
                    ),
                },
            }

        if state == "failed":
            return {
                "status": "error",
                "message": "SSH service has failed",
                "data": {
                    "service": service_name,
                    "state": "failed",
                    "port": 22,
                    "configuration": (
                        "read-only inspection"
                    ),
                },
            }

    config_paths = [
        Path("/etc/ssh/sshd_config"),
        Path("/etc/sshd_config"),
    ]

    existing = [
        str(path)
        for path in config_paths
        if path.exists()
    ]

    if existing:
        return {
            "status": "warning",
            "message": (
                "SSH configuration detected, "
                "but service state could not be determined"
            ),
            "data": {
                "service": None,
                "state": "unknown",
                "port": 22,
                "configuration": existing,
            },
        }

    return {
        "status": "unknown",
        "message": (
            "SSH service/configuration not detected"
        ),
        "data": {
            "service": None,
            "state": "unknown",
            "port": 22,
            "configuration": [],
        },
    }


# ============================================================
# FIREWALL
# ============================================================

def check_firewall():
    """Inspect firewall state without modifying configuration."""

    checks = []

    # --------------------------------------------------------
    # UFW
    # --------------------------------------------------------

    ufw = _run(["ufw", "status"])

    if ufw["available"]:

        output = (
            ufw["stdout"]
            if ufw["returncode"] == 0
            else ufw["stderr"]
        )

        lowered = output.lower()

        insufficient = (
            ufw["returncode"] != 0
            and (
                "you need to be root" in lowered
                or "permission denied" in lowered
                or "operation not permitted" in lowered
            )
        )

        if insufficient:
            state = "unknown"
            inspection = "insufficient_privileges"

        elif (
            ufw["returncode"] == 0
            and "status: active" in lowered
        ):
            state = "active"
            inspection = "completed"

        elif (
            ufw["returncode"] == 0
            and "status: inactive" in lowered
        ):
            state = "inactive"
            inspection = "completed"

        else:
            state = "unknown"
            inspection = "completed"

        checks.append(
            {
                "name": "ufw",
                "available": True,
                "status": output,
                "state": state,
                "inspection": inspection,
                "returncode": ufw["returncode"],
            }
        )

    # --------------------------------------------------------
    # FIREWALLD
    # --------------------------------------------------------

    firewalld = _run(
        [
            "firewall-cmd",
            "--state",
        ]
    )

    if firewalld["available"]:

        output = (
            firewalld["stdout"]
            if firewalld["returncode"] == 0
            else firewalld["stderr"]
        )

        lowered = output.lower()

        insufficient = (
            firewalld["returncode"] != 0
            and (
                "permission denied" in lowered
                or "operation not permitted" in lowered
                or "not authorized" in lowered
            )
        )

        if insufficient:
            state = "unknown"
            inspection = "insufficient_privileges"

        elif (
            firewalld["returncode"] == 0
            and firewalld["stdout"].strip() == "running"
        ):
            state = "active"
            inspection = "completed"

        elif firewalld["returncode"] == 0:
            state = "inactive"
            inspection = "completed"

        else:
            state = "unknown"
            inspection = "completed"

        checks.append(
            {
                "name": "firewalld",
                "available": True,
                "status": output,
                "state": state,
                "inspection": inspection,
                "returncode": firewalld["returncode"],
            }
        )

    # --------------------------------------------------------
    # NFTABLES
    # --------------------------------------------------------

    nft = _run(
        [
            "nft",
            "list",
            "ruleset",
        ]
    )

    if nft["available"]:

        output = (
            "ruleset available"
            if nft["returncode"] == 0
            else nft["stderr"]
        )

        lowered = output.lower()

        insufficient = (
            nft["returncode"] != 0
            and (
                "operation not permitted" in lowered
                or "you must be root" in lowered
                or "permission denied" in lowered
            )
        )

        if insufficient:
            state = "unknown"
            inspection = "insufficient_privileges"

        elif nft["returncode"] == 0:
            state = "active"
            inspection = "completed"

        else:
            state = "inactive"
            inspection = "completed"

        checks.append(
            {
                "name": "nftables",
                "available": True,
                "status": output,
                "state": state,
                "inspection": inspection,
                "returncode": nft["returncode"],
            }
        )

    # --------------------------------------------------------
    # NO SUPPORTED FIREWALL
    # --------------------------------------------------------

    if not checks:
        return {
            "status": "unknown",
            "message": (
                "No supported firewall tool detected"
            ),
            "data": [],
        }

    active = any(
        item["state"] == "active"
        for item in checks
    )

    insufficient = any(
        item["inspection"]
        == "insufficient_privileges"
        for item in checks
    )

    unknown = any(
        item["state"] == "unknown"
        for item in checks
    )

    inactive = all(
        item["state"] == "inactive"
        for item in checks
    )

    if active:
        status = "healthy"
        message = "Firewall protection detected"

    elif insufficient:
        status = "unknown"
        message = (
            "Firewall state could not be determined: "
            "insufficient privileges"
        )

    elif unknown:
        status = "unknown"
        message = (
            "Firewall state could not be determined"
        )

    elif inactive:
        status = "warning"
        message = "No active firewall detected"

    else:
        status = "unknown"
        message = (
            "Firewall state could not be determined"
        )

    return {
        "status": status,
        "message": message,
        "data": checks,
    }


# ============================================================
# SYSTEM
# ============================================================

def check_system():
    """Inspect local system security context."""

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
                "user": user,
                "os": platform.system(),
                "platform": platform.system().lower(),
                "release": platform.release(),
                "architecture": platform.machine(),
            },
        }

    except Exception as exc:

        return {
            "status": "error",
            "message": str(exc),
            "data": {},
        }


# ============================================================
# FILE PERMISSIONS
# ============================================================

def _permission_string(mode):
    """Convert file mode to readable permissions."""

    return stat.filemode(mode)


def _inspect_file_permission(path, expected_mode):
    """
    Inspect file metadata only.

    Never reads file contents.
    """

    path = Path(path)

    result = {
        "path": str(path),
        "exists": path.exists(),
        "expected": expected_mode,
        "mode": None,
        "permissions": None,
        "owner": None,
        "group": None,
        "status": "unknown",
    }

    if not path.exists():

        result["status"] = "not_found"

        return result

    try:

        info = path.stat()

        mode = stat.S_IMODE(
            info.st_mode
        )

        result["mode"] = oct(mode)

        result["permissions"] = (
            _permission_string(info.st_mode)
        )

        try:
            result["owner"] = pwd.getpwuid(
                info.st_uid
            ).pw_name
        except Exception:
            result["owner"] = str(info.st_uid)

        try:
            result["group"] = grp.getgrgid(
                info.st_gid
            ).gr_name
        except Exception:
            result["group"] = str(info.st_gid)

        expected = int(
            expected_mode,
            8
        )

        result["status"] = (
            "healthy"
            if mode == expected
            else "warning"
        )

        return result

    except PermissionError:

        result["status"] = "unknown"

        return result

    except Exception:

        result["status"] = "error"

        return result


def check_file_permissions():
    """
    Inspect security-sensitive file permissions.

    Read-only.

    File contents are never read.
    """

    targets = [
        ("/etc/passwd", "644"),
        ("/etc/shadow", "640"),
        ("/etc/group", "644"),
        ("/etc/sudoers", "440"),
        ("/etc/ssh/sshd_config", "644"),
        ("/etc/systemd/system/veles.service", "644"),
    ]

    results = [
        _inspect_file_permission(
            path,
            expected,
        )
        for path, expected in targets
    ]

    existing = [
        item
        for item in results
        if item["status"] != "not_found"
    ]

    warnings = [
        item
        for item in existing
        if item["status"] == "warning"
    ]

    errors = [
        item
        for item in existing
        if item["status"] == "error"
    ]

    unknown = [
        item
        for item in existing
        if item["status"] == "unknown"
    ]

    if errors:

        status = "error"

        message = (
            f"{len(errors)} permission "
            "inspection error(s)"
        )

    elif warnings:

        status = "warning"

        message = (
            f"{len(warnings)} file permission "
            "warning(s)"
        )

    elif unknown:

        status = "unknown"

        message = (
            f"{len(unknown)} file permission "
            "check(s) could not be completed"
        )

    else:

        status = "healthy"

        message = (
            f"Checked {len(existing)} "
            "security-sensitive files"
        )

    return {
        "status": status,
        "message": message,
        "data": results,
    }
