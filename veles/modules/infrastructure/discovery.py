"""
Veles Infrastructure Discovery

Dynamic network discovery for:

- Ethernet / LAN
- Wi-Fi
- VPN
- WireGuard
- Tailscale
- tun/tap
- other IPv4 interfaces
- routed IPv4 networks

Discovery never registers resources automatically.
"""

import ipaddress
import platform
import shutil
import socket
import subprocess

from concurrent.futures import ThreadPoolExecutor, as_completed

from .models import Server


# ============================================================
# LOCAL SYSTEM
# ============================================================

def get_hostname():
    return socket.gethostname()


def get_ip():
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

    except Exception:
        return "unknown"

    for line in result.splitlines():

        parts = line.split()

        if len(parts) < 4:
            continue

        interface = parts[1]

        if interface == "lo":
            continue

        address = parts[3]

        try:
            ip_interface = ipaddress.ip_interface(address)

        except ValueError:
            continue

        if (
            ip_interface.version == 4
            and not ip_interface.ip.is_loopback
        ):
            return str(ip_interface.ip)

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

        total = (
            meminfo["MemTotal"]
            / 1024
            / 1024
        )

        available = (
            meminfo["MemAvailable"]
            / 1024
            / 1024
        )

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

        days = int(
            seconds // 86400
        )

        hours = int(
            (seconds % 86400) // 3600
        )

        return f"{days}d {hours}h"

    except Exception:

        return "unknown"


def discover_local_server():

    hostname = get_hostname()

    server = Server(
        name=hostname,
        hostname=hostname,
        ip=get_ip(),
        os=platform.platform()
    )

    server.cpu = get_cpu()
    server.memory = get_memory()
    server.disk = get_disk_usage()
    server.uptime = get_uptime()

    server.touch()

    return server


# ============================================================
# NETWORK TARGET DISCOVERY
# ============================================================

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

    if ip_interface.version != 4:
        return None

    target = {

        "interface": interface,

        "address": str(
            ip_interface
        ),

        "network": str(
            ip_interface.network
        ),

        "prefix": ip_interface.network.prefixlen,

        "source": source,

        "scannable": True

    }

    return target


def _build_route_target(
    interface,
    network,
    source="route"
):

    try:

        target_network = ipaddress.ip_network(
            network,
            strict=False
        )

    except ValueError:

        return None

    if target_network.version != 4:
        return None

    # A /32 route represents a single host, not a
    # network that discover_network_hosts() can scan.
    if target_network.prefixlen == 32:
        return None

    return {

        "interface": interface or "Routed Network",

        "address": str(target_network),

        "network": str(target_network),

        "prefix": target_network.prefixlen,

        "source": source,

        "scannable": True

    }


def discover_routing_targets():

    """
    Discover IPv4 networks available through the
    current Linux routing table.

    No network, gateway, interface or VPN is hardcoded.

    The default route is intentionally ignored because
    it represents the Internet rather than a finite
    network that should be scanned.
    """

    targets = []

    try:

        result = subprocess.check_output(
            [
                "ip",
                "-4",
                "route",
                "show"
            ],
            text=True
        )

    except Exception as e:

        print(
            "Routing target discovery error:",
            e
        )

        return targets

    for line in result.splitlines():

        line = line.strip()

        if not line:
            continue

        parts = line.split()

        if not parts:
            continue

        destination = parts[0]

        # Never interpret the default route as a
        # scan target.
        if destination == "default":
            continue

        try:

            network = ipaddress.ip_network(
                destination,
                strict=False
            )

        except ValueError:

            continue

        if network.version != 4:
            continue

        # Host routes are not network scan targets.
        if network.prefixlen == 32:
            continue

        interface = None

        if "dev" in parts:

            index = parts.index("dev")

            if index + 1 < len(parts):

                interface = parts[index + 1]

        target = _build_route_target(
            interface=interface,
            network=str(network),
            source="route"
        )

        if target:
            targets.append(target)

    return targets


def discover_network_targets(
    custom_networks=None
):

    """
    Discover every IPv4 network currently reachable
    through the local system.

    Sources:

    1. Directly configured IPv4 interfaces.
    2. IPv4 routing table.
    3. User-defined custom networks.

    No interface names, IP addresses or networks
    are hardcoded.

    VPNs, WireGuard, Tailscale, tunnels, VLANs,
    bridges and other network paths are discovered
    when the operating system exposes them through
    interfaces or routes.
    """

    targets = []

    seen = set()

    custom_networks = custom_networks or []

    # ========================================================
    # DIRECTLY CONFIGURED INTERFACES
    # ========================================================

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
            source="interface"
        )

        if not target:
            continue

        # A /32 interface address does not define a
        # finite network to scan.
        if target["prefix"] == 32:
            continue

        identity = (
            target["network"]
        )

        if identity in seen:
            continue

        seen.add(identity)

        targets.append(target)

    # ========================================================
    # ROUTING TABLE
    # ========================================================

    routing_targets = discover_routing_targets()

    for target in routing_targets:

        identity = (
            target["network"]
        )

        if identity in seen:
            continue

        seen.add(identity)

        targets.append(target)

    # ========================================================
    # CUSTOM NETWORKS
    # ========================================================

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

        if network.version != 4:
            continue

        network_string = str(network)

        identity = (
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


# ============================================================
# INTERFACE / ROUTING
# ============================================================

def get_interface_for_network(network):

    """
    Finds the interface used to reach the network.

    First checks directly configured interfaces.
    Then asks Linux routing table.
    """

    try:

        target_network = ipaddress.ip_network(
            network,
            strict=False
        )

    except ValueError:

        return None

    # --------------------------------------------------------
    # DIRECTLY CONFIGURED NETWORK
    # --------------------------------------------------------

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

    except Exception:

        result = ""

    for line in result.splitlines():

        parts = line.split()

        if len(parts) < 4:
            continue

        interface = parts[1]

        if interface == "lo":
            continue

        address = parts[3]

        try:

            ip_interface = ipaddress.ip_interface(
                address
            )

        except ValueError:

            continue

        if ip_interface.ip in target_network:

            return interface

    # --------------------------------------------------------
    # ROUTING TABLE
    # --------------------------------------------------------

    try:

        route = subprocess.check_output(
            [
                "ip",
                "-4",
                "route",
                "get",
                str(target_network.network_address)
            ],
            text=True
        )

        parts = route.split()

        if "dev" in parts:

            index = parts.index("dev")

            if index + 1 < len(parts):

                return parts[index + 1]

    except Exception as e:

        print(
            "Route interface detection error:",
            e
        )

    return None


def get_interface_type(interface):

    """
    Determines whether an interface is likely
    Ethernet/Wi-Fi or virtual/VPN.

    This is informational only.
    """

    if not interface:
        return "unknown"

    try:

        result = subprocess.run(
            [
                "ip",
                "-d",
                "link",
                "show",
                "dev",
                interface
            ],
            capture_output=True,
            text=True,
            timeout=3
        )

        output = result.stdout.lower()

    except Exception:

        return "unknown"

    if "wireguard" in output:
        return "wireguard"

    if "tun" in interface.lower():
        return "vpn"

    if "tap" in interface.lower():
        return "vpn"

    if "tailscale" in interface.lower():
        return "tailscale"

    if "ether" in output:
        return "ethernet"

    if "wifi" in output:
        return "wifi"

    if "wireless" in output:
        return "wifi"

    return "virtual"


# ============================================================
# ARP
# ============================================================

def get_arp_hosts(
    interface,
    network
):

    """
    Reads Linux neighbor table.

    Used primarily for local L2 networks.

    VPN interfaces normally do not expose
    useful ARP entries, so an empty result
    simply causes IP discovery fallback.
    """

    try:

        target_network = ipaddress.ip_network(
            network,
            strict=False
        )

        result = subprocess.run(
            [
                "ip",
                "neigh",
                "show",
                "dev",
                interface
            ],
            capture_output=True,
            text=True,
            timeout=5
        )

    except Exception as e:

        print(
            "ARP discovery error:",
            e
        )

        return []

    hosts = []

    for line in result.stdout.splitlines():

        parts = line.split()

        if len(parts) < 2:
            continue

        address = parts[0]

        try:

            ip = ipaddress.ip_address(
                address
            )

        except ValueError:

            continue

        if ip.version != 4:
            continue

        if ip not in target_network:
            continue

        if ip.is_loopback:
            continue

        state = parts[-1].upper()

        if state in (
            "FAILED",
            "INCOMPLETE"
        ):
            continue

        hosts.append(
            str(ip)
        )

    return sorted(
        set(hosts),
        key=lambda value: ipaddress.ip_address(value)
    )


# ============================================================
# HOST DISCOVERY
# ============================================================

def check_port(
    host,
    port,
    timeout=0.25
):

    try:

        with socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        ) as sock:

            sock.settimeout(timeout)

            return (
                sock.connect_ex(
                    (
                        host,
                        port
                    )
                ) == 0
            )

    except Exception:

        return False


def ping_host(
    ip,
    timeout=0.5
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
            stderr=subprocess.DEVNULL,
            timeout=timeout + 0.5
        )

        return result.returncode == 0

    except Exception:

        return False


def scan_host(
    ip,
    services
):

    ip = str(ip)

    found_services = []

    ping_alive = ping_host(ip)

    for port, name in services.items():

        if check_port(
            ip,
            port
        ):

            found_services.append({
                "service": name,
                "port": port
            })

    # Host is discovered if:
    #
    # - ICMP responds
    # - OR known TCP service responds

    if not ping_alive and not found_services:
        return None

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

        "status": "alive"

    }


# ============================================================
# NETWORK DISCOVERY
# ============================================================

def discover_network_hosts(
    network,
    progress_callback=None
):

    """
    Discover hosts inside a network.

    Strategy:

    1. Determine actual Linux interface.
    2. Try ARP neighbor discovery.
    3. If ARP has entries, scan those hosts.
    4. Otherwise scan the CIDR directly.

    Works with any IPv4 network that is
    reachable through the current system.
    """

    services = {

        22: "SSH",

        5985: "WinRM",

        5986: "WinRM SSL",

        3389: "RDP",

        445: "SMB"

    }

    try:

        net = ipaddress.ip_network(
            network,
            strict=False
        )

    except ValueError:

        return []

    if net.version != 4:

        return []

    interface = get_interface_for_network(
        network
    )

    interface_type = get_interface_type(
        interface
    )

    print(
        "Discovery target:",
        network
    )

    print(
        "Interface:",
        interface
    )

    print(
        "Interface type:",
        interface_type
    )

    addresses = []

    # ========================================================
    # ARP
    # ========================================================

    arp_hosts = []

    if interface:

        arp_hosts = get_arp_hosts(
            interface,
            network
        )

    if arp_hosts:

        addresses = arp_hosts

        print(
            "Using neighbor discovery:",
            interface,
            network,
            "hosts:",
            len(addresses)
        )

    # ========================================================
    # DIRECT IP SCAN
    # ========================================================

    if not addresses:

        addresses = [
            str(ip)
            for ip in net.hosts()
        ]

        print(
            "Using IP discovery:",
            network,
            "interface:",
            interface,
            "type:",
            interface_type,
            "hosts:",
            len(addresses)
        )

    # ========================================================
    # PROGRESS
    # ========================================================

    total = len(addresses)

    checked = 0

    hosts = []

    if progress_callback:

        progress_callback({

            "running": True,

            "network": network,

            "total": total,

            "checked": 0,

            "found": 0

        })

    # ========================================================
    # PARALLEL SCAN
    # ========================================================

    with ThreadPoolExecutor(
        max_workers=50
    ) as executor:

        futures = [

            executor.submit(
                scan_host,
                ip,
                services
            )

            for ip in addresses

        ]

        for future in as_completed(
            futures
        ):

            try:

                result = future.result()

            except Exception as e:

                print(
                    "Discovery worker error:",
                    e
                )

                result = None

            checked += 1

            if result:

                hosts.append(
                    result
                )

            if progress_callback:

                progress_callback({

                    "running": True,

                    "network": network,

                    "total": total,

                    "checked": checked,

                    "found": len(hosts)

                })

    # ========================================================
    # SORT
    # ========================================================

    hosts.sort(
        key=lambda item:
        ipaddress.ip_address(
            item["host"]
        )
    )

    # ========================================================
    # COMPLETE
    # ========================================================

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
        "Discovery complete:",
        network,
        "found:",
        len(hosts)
    )

    return hosts