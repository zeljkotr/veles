"""
VELES Security Checks

Read-only local security inspection.

The module never changes system configuration.
"""

import os
import pwd
import socket
import stat
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

    Firewall state is reported as unknown when the
    current VELES service user lacks the privileges
    required to inspect firewall state.
    """

    checks = []

    ufw = _run(
        [
            "ufw",
            "status"
        ]
    )

    if ufw["available"]:

        status = (
            ufw["stdout"]
            if ufw["returncode"] == 0
            else ufw["stderr"]
        )

        insufficient_privileges = (
            ufw["returncode"] != 0
            and (
                "you need to be root" in status.lower()
                or "permission denied" in status.lower()
                or "operation not permitted" in status.lower()
            )
        )

        checks.append(
            {
                "name": "ufw",
                "available": True,
                "status": status,
                "state": (
                    "unknown"
                    if insufficient_privileges
                    else (
                        "active"
                        if ufw["returncode"] == 0
                        and "status: active" in status.lower()
                        else "inactive"
                    )
                ),
                "inspection": (
                    "insufficient_privileges"
                    if insufficient_privileges
                    else "completed"
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

        status = (
            firewall_cmd["stdout"]
            if firewall_cmd["returncode"] == 0
            else firewall_cmd["stderr"]
        )

        insufficient_privileges = (
            firewall_cmd["returncode"] != 0
            and (
                "permission denied" in status.lower()
                or "operation not permitted" in status.lower()
                or "not authorized" in status.lower()
            )
        )

        checks.append(
            {
                "name": "firewalld",
                "available": True,
                "status": status,
                "state": (
                    "unknown"
                    if insufficient_privileges
                    else (
                        "active"
                        if firewall_cmd["returncode"] == 0
                        and firewall_cmd["stdout"].strip() == "running"
                        else "inactive"
                    )
                ),
                "inspection": (
                    "insufficient_privileges"
                    if insufficient_privileges
                    else "completed"
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

        status = (
            "ruleset available"
            if nft["returncode"] == 0
            else nft["stderr"]
        )

        insufficient_privileges = (
            nft["returncode"] != 0
            and (
                "operation not permitted" in status.lower()
                or "you must be root" in status.lower()
                or "permission denied" in status.lower()
            )
        )

        checks.append(
            {
                "name": "nftables",
                "available": True,
                "status": status,
                "state": (
                    "unknown"
                    if insufficient_privileges
                    else (
                        "active"
                        if nft["returncode"] == 0
                        else "inactive"
                    )
                ),
                "inspection": (
                    "insufficient_privileges"
                    if insufficient_privileges
                    else "completed"
                ),
                "returncode": nft["returncode"]
            }
        )

    if not checks:

        return {
            "status": "unknown",
            "message": (
                "No supported firewall tool detected"
            ),
            "data": []
        }

    insufficient_privileges = any(
        check.get("inspection") == "insufficient_privileges"
        for check in checks
    )

    active = any(
        check.get("state") == "active"
        for check in checks
    )

    if active:

        status = "healthy"

        message = (
            "Firewall protection detected"
        )

    elif insufficient_privileges:

        status = "unknown"

        message = (
            "Firewall state could not be determined: "
            "insufficient privileges"
        )

    else:

        status = "warning"

        message = (
            "No active firewall detected"
        )

    return {
        "status": status,
        "message": message,
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


def _permission_string(mode):
    """
    Convert a file mode to a readable permission string.
    """

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
        "status": "unknown"
    }

    if not path.exists():

        result["status"] = "not_found"

        return result

    try:

        info = path.stat()

        mode = stat.S_IMODE(info.st_mode)

        result["mode"] = oct(mode)
        result["permissions"] = _permission_string(
            info.st_mode
        )

        try:
            result["owner"] = pwd.getpwuid(
                info.st_uid
            ).pw_name

        except Exception:
            result["owner"] = str(info.st_uid)

        try:

            import grp

            result["group"] = grp.getgrgid(
                info.st_gid
            ).gr_name

        except Exception:

            result["group"] = str(info.st_gid)

        expected = int(
            expected_mode,
            8
        )

        if mode == expected:

            result["status"] = "healthy"

        else:

            result["status"] = "warning"

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
        (
            "/etc/passwd",
            "644"
        ),
        (
            "/etc/shadow",
            "640"
        ),
        (
            "/etc/group",
            "644"
        ),
        (
            "/etc/sudoers",
            "440"
        ),
        (
            "/etc/ssh/sshd_config",
            "644"
        ),
        (
            "/etc/systemd/system/veles.service",
            "644"
        )
    ]

    results = [
        _inspect_file_permission(
            path,
            expected
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
            f"{len(errors)} permission inspection error(s)"
        )

    elif warnings:

        status = "warning"

        message = (
            f"{len(warnings)} file permission warning(s)"
        )

    elif unknown:

        status = "unknown"

        message = (
            f"{len(unknown)} file permission check(s) "
            "could not be completed"
        )

    else:

        status = "healthy"

        message = (
            f"Checked {len(existing)} security-sensitive files"
        )

    return {
        "status": status,
        "message": message,
        "data": results
    }