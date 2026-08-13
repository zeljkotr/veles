"""
Veles Infrastructure Discovery

Prikupljanje osnovnih podataka
lokalnog sistema i mrežni discovery.
"""

import platform
import socket
import shutil
import ipaddress
import subprocess

from concurrent.futures import ThreadPoolExecutor, as_completed

from .models import Server


def get_hostname():
    return socket.gethostname()


def get_ip():
    try:
        s = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        s.connect(
            ("8.8.8.8", 80)
        )

        ip = s.getsockname()[0]

        s.close()

        return ip

    except Exception:
        return "unknown"


def get_cpu():
    try:
        with open("/proc/loadavg", "r") as f:
            return f.read().split()[0]

    except Exception:
        return "unknown"


def get_memory():
    try:
        meminfo = {}

        with open("/proc/meminfo", "r") as f:

            for line in f:

                key, value = line.split(":", 1)

                meminfo[key] = int(
                    value.strip().split()[0]
                )

        total = meminfo["MemTotal"] / 1024 / 1024

        available = meminfo["MemAvailable"] / 1024 / 1024

        used = total - available

        return {
            "total_gb": round(total, 2),
            "used_gb": round(used, 2),
            "free_gb": round(available, 2)
        }

    except Exception:
        return {
            "total_gb": 0,
            "used_gb": 0,
            "free_gb": 0
        }


def get_disk_usage():

    total, used, free = shutil.disk_usage("/")

    return {
        "total_gb": round(
            total / (1024 ** 3),
            2
        ),

        "used_gb": round(
            used / (1024 ** 3),
            2
        ),

        "free_gb": round(
            free / (1024 ** 3),
            2
        )
    }


def get_uptime():
    try:

        with open("/proc/uptime", "r") as f:

            seconds = float(
                f.read().split()[0]
            )

        days = int(seconds // 86400)

        hours = int(
            (seconds % 86400) // 3600
        )

        return f"{days}d {hours}h"

    except Exception:

        return "unknown"


def discover_local_server():

    server = Server(
        name="Veles Core",
        hostname=get_hostname(),
        ip=get_ip(),
        os=platform.platform()
    )

    server.cpu = get_cpu()

    server.memory = get_memory()

    server.disk = get_disk_usage()

    server.uptime = get_uptime()

    server.touch()

    return server


def _build_network_target(
    interface,
    address,
    source="auto"
):

    try:

        ip_interface = ipaddress.ip_interface(
            address
        )

    except ValueError:

        return None

    network = ip_interface.network

    prefix = ip_interface.network.prefixlen

    target = {
        "interface": interface,
        "address": str(ip_interface),
        "network": str(network),
        "prefix": prefix,
        "source": source,
        "scannable": True
    }

    """
    A /32 IPv4 address identifies a single host,
    not a usable multi-host network discovery scope.

    Keep the interface visible, but do not automatically
    turn the /32 into a network scan target.
    """

    if (
        ip_interface.version == 4
        and prefix == 32
    ):

        target["network"] = None

        target["scannable"] = False

    return target


def discover_network_targets(
    custom_networks=None
):

    """
    Pronalazi mrežne targete.

    AUTO:
        Čita stvarne IPv4 adrese koje OS prijavi.

    CUSTOM:
        Dodaje CIDR mreže koje korisnik ručno unese.

    Ne skenira.
    Ne dodaje resurse.
    """

    targets = []

    seen = set()

    custom_networks = custom_networks or []

    try:

        result = subprocess.check_output(
            [
                "ip",
                "-o",
                "-4",
                "addr"
            ],
            text=True
        )

    except Exception as e:

        print(
            "Network target discovery error:",
            e
        )

        result = ""

    for line in result.splitlines():

        parts = line.split()

        if len(parts) < 4:
            continue

        interface = parts[1]

        if interface == "lo":
            continue

        address = parts[3]

        target = _build_network_target(
            interface=interface,
            address=address,
            source="auto"
        )

        if not target:
            continue

        identity = (
            target["interface"],
            target["address"]
        )

        if identity in seen:
            continue

        seen.add(identity)

        targets.append(target)

    for value in custom_networks:

        if not value:
            continue

        value = value.strip()

        try:

            network = ipaddress.ip_network(
                value,
                strict=False
            )

        except ValueError:

            continue

        network_string = str(network)

        identity = (
            "custom",
            network_string
        )

        if identity in seen:
            continue

        seen.add(identity)

        targets.append({
            "interface": "Custom Network",
            "address": network_string,
            "network": network_string,
            "prefix": network.prefixlen,
            "source": "custom",
            "scannable": True
        })

    return targets


def check_port(
    host,
    port,
    timeout=0.2
):

    try:

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        sock.settimeout(timeout)

        result = sock.connect_ex(
            (
                host,
                port
            )
        )

        sock.close()

        return result == 0

    except Exception:

        return False


def ping_host(
    ip,
    timeout=1
):

    try:

        result = subprocess.run(
            [
                "ping",
                "-c",
                "1",
                "-W",
                str(timeout),
                str(ip)
            ],

            stdout=subprocess.DEVNULL,

            stderr=subprocess.DEVNULL
        )

        return result.returncode == 0

    except Exception:

        return False


def scan_host(
    ip,
    services,
    cancel_event=None
):

    if (
        cancel_event
        and cancel_event.is_set()
    ):

        return None

    ip = str(ip)

    found_services = []

    if not ping_host(ip):

        return None

    if (
        cancel_event
        and cancel_event.is_set()
    ):

        return None

    for port, name in services.items():

        if (
            cancel_event
            and cancel_event.is_set()
        ):

            return None

        if check_port(
            ip,
            port
        ):

            found_services.append({
                "service": name,
                "port": port
            })

    return {
        "type": "server",

        "name": f"Discovered-{ip}",

        "host": ip,

        "os": "unknown",

        "port": (
            found_services[0]["port"]
            if found_services
            else None
        ),

        "services": found_services,

        "status": "alive",

        "group": "network"
    }


def discover_network_hosts(
    network,
    progress_callback=None,
    cancel_event=None
):

    """
    Network discovery.

    Ping + service detection.

    Supports cancellation through
    threading.Event().
    """

    hosts = []

    services = {
        22: "SSH",
        5985: "WinRM",
        5986: "WinRM SSL",
        3389: "RDP",
        445: "SMB"
    }

    net = ipaddress.ip_network(
        network,
        strict=False
    )

    addresses = list(
        net.hosts()
    )

    total = len(addresses)

    checked = 0

    if progress_callback:

        progress_callback({
            "running": True,
            "network": network,
            "total": total,
            "checked": 0,
            "found": 0
        })

    print(
        "Starting scan:",
        network,
        "hosts:",
        total
    )

    with ThreadPoolExecutor(
        max_workers=50
    ) as executor:

        futures = []

        for ip in addresses:

            if (
                cancel_event
                and cancel_event.is_set()
            ):

                break

            futures.append(
                executor.submit(
                    scan_host,
                    ip,
                    services,
                    cancel_event
                )
            )

        for future in as_completed(futures):

            if (
                cancel_event
                and cancel_event.is_set()
            ):

                break

            try:

                result = future.result()

            except Exception as e:

                print(
                    "DISCOVERY HOST ERROR:",
                    e
                )

                result = None

            checked += 1

            if result:

                hosts.append(result)

            if progress_callback:

                progress_callback({
                    "running": True,
                    "network": network,
                    "total": total,
                    "checked": checked,
                    "found": len(hosts)
                })

    if (
        cancel_event
        and cancel_event.is_set()
    ):

        if progress_callback:

            progress_callback({
                "running": False,
                "cancelled": True,
                "network": network,
                "total": total,
                "checked": checked,
                "found": len(hosts),
                "results": hosts
            })

        print(
            "Scan cancelled:",
            network,
            "checked:",
            checked,
            "found:",
            len(hosts)
        )

        return hosts

    if progress_callback:

        progress_callback({
            "running": False,
            "network": network,
            "total": total,
            "checked": checked,
            "found": len(hosts),
            "results": hosts
        })

    print(
        "Scan complete:",
        network,
        "checked:",
        checked,
        "found:",
        len(hosts)
    )

    return hosts