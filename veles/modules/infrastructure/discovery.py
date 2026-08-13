"""
Veles Infrastructure Discovery

Prikupljanje osnovnih podataka lokalnog sistema
i mrežni discovery.

Discovery pokušava da identifikuje uređaje kao:

- computer
- laptop
- phone
- tv
- camera
- printer
- router
- network_device
- iot
- server
- unknown

Discovery nikada automatski ne registruje resurse.

Arhitektura:

FAST DISCOVERY
    ->
lista pronađenih hostova
    ->
DETAILS
    ->
DEEP NMAP SCAN samo jednog hosta
"""

import platform
import socket
import shutil
import ipaddress
import subprocess
import re

from concurrent.futures import ThreadPoolExecutor, as_completed

from .models import Server


# ============================================================
# LOCAL SYSTEM
# ============================================================

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

        with open(
            "/proc/loadavg",
            "r"
        ) as f:

            return f.read().split()[0]

    except Exception:

        return "unknown"


def get_memory():

    try:

        meminfo = {}

        with open(
            "/proc/meminfo",
            "r"
        ) as f:

            for line in f:

                key, value = line.split(
                    ":",
                    1
                )

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
            "total_gb": round(
                total,
                2
            ),
            "used_gb": round(
                used,
                2
            ),
            "free_gb": round(
                available,
                2
            )
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

        with open(
            "/proc/uptime",
            "r"
        ) as f:

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


# ============================================================
# NETWORK TARGETS
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

    network = ip_interface.network

    prefix = ip_interface.network.prefixlen

    target = {

        "interface": interface,

        "address": str(
            ip_interface
        ),

        "network": str(
            network
        ),

        "prefix": prefix,

        "source": source,

        "scannable": True

    }

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


# ============================================================
# BASIC NETWORK TESTS
# ============================================================

def check_port(
    host,
    port,
    timeout=0.35
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


# ============================================================
# HOSTNAME
# ============================================================

def resolve_hostname(ip):

    try:

        hostname = socket.gethostbyaddr(
            ip
        )[0]

        if hostname:

            return hostname

    except Exception:

        pass

    return None


# ============================================================
# ARP / NEIGHBOR INFORMATION
# ============================================================

def get_neighbor_info(ip):

    """
    Pokušava da pronađe MAC adresu preko Linux neighbor
    tabele.

    Primer:

        192.168.2.22 dev eth0 lladdr aa:bb:cc:dd:ee:ff REACHABLE
    """

    try:

        result = subprocess.run(
            [
                "ip",
                "neigh",
                "show",
                ip
            ],

            capture_output=True,

            text=True,

            timeout=2
        )

        output = result.stdout.strip()

        if not output:

            return {
                "mac": None,
                "state": None,
                "interface": None
            }

        mac_match = re.search(
            r"lladdr\s+([0-9a-fA-F:]{17})",
            output
        )

        state_match = re.search(
            r"\b(REACHABLE|STALE|DELAY|PROBE|FAILED|INCOMPLETE|NOARP|PERMANENT)\b",
            output
        )

        interface_match = re.search(
            r"\bdev\s+(\S+)",
            output
        )

        return {

            "mac": (
                mac_match.group(1).lower()
                if mac_match
                else None
            ),

            "state": (
                state_match.group(1).lower()
                if state_match
                else None
            ),

            "interface": (
                interface_match.group(1)
                if interface_match
                else None
            )

        }

    except Exception:

        return {
            "mac": None,
            "state": None,
            "interface": None
        }


# ============================================================
# HTTP / SERVICE DETECTION
# ============================================================

def http_probe(
    host,
    port,
    timeout=1.0
):

    try:

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        sock.settimeout(timeout)

        sock.connect(
            (
                host,
                port
            )
        )

        request = (
            f"GET / HTTP/1.0\r\n"
            f"Host: {host}\r\n"
            f"User-Agent: Veles-Discovery\r\n"
            f"Connection: close\r\n\r\n"
        )

        sock.sendall(
            request.encode(
                "ascii",
                errors="ignore"
            )
        )

        data = sock.recv(
            4096
        )

        sock.close()

        return data.decode(
            "latin-1",
            errors="ignore"
        )

    except Exception:

        return ""


def detect_http_identity(
    host,
    port
):

    response = http_probe(
        host,
        port
    )

    if not response:

        return {
            "server": None,
            "headers": {}
        }

    lines = response.splitlines()

    server = None

    headers = {}

    for line in lines:

        if ":" not in line:
            continue

        key, value = line.split(
            ":",
            1
        )

        key = key.strip().lower()

        value = value.strip()

        headers[key] = value

        if key == "server":

            server = value

    return {
        "server": server,
        "headers": headers
    }


# ============================================================
# DEVICE CLASSIFICATION
# ============================================================

def classify_device(
    host,
    hostname,
    open_ports,
    services,
    http_identity=None
):

    """
    Procena tipa uređaja.

    Ovo je fingerprinting, ne apsolutna istina.

    Prioritet:

        camera
        printer
        router/network_device
        tv
        phone
        server
        computer
        iot
        unknown
    """

    ports = set(
        open_ports
    )

    service_names = {
        str(item.get("service", "")).lower()
        for item in services
    }

    hostname_text = (
        hostname or ""
    ).lower()

    http_server = ""

    if http_identity:

        http_server = (
            http_identity.get(
                "server"
            )
            or ""
        ).lower()

    fingerprint = (
        hostname_text
        + " "
        + http_server
    )

    # --------------------------------------------------------
    # CAMERA
    # --------------------------------------------------------

    camera_ports = {
        554,
        8554,
        8000,
        8080
    }

    camera_words = (
        "camera",
        "cam",
        "ipc",
        "dvr",
        "nvr",
        "hikvision",
        "dahua",
        "reolink",
        "axis",
        "uniview"
    )

    if (
        ports.intersection(
            camera_ports
        )
        and (
            "rtsp" in service_names
            or any(
                word in fingerprint
                for word in camera_words
            )
        )
    ):

        return "camera"

    if any(
        word in fingerprint
        for word in camera_words
    ):

        return "camera"

    # --------------------------------------------------------
    # PRINTER
    # --------------------------------------------------------

    printer_ports = {
        515,
        631,
        9100
    }

    printer_words = (
        "printer",
        "print",
        "epson",
        "canon",
        "brother",
        "lexmark",
        "xerox",
        "hp-",
        "laserjet",
        "deskjet"
    )

    if ports.intersection(
        printer_ports
    ):

        return "printer"

    if any(
        word in fingerprint
        for word in printer_words
    ):

        return "printer"

    # --------------------------------------------------------
    # ROUTER / NETWORK DEVICE
    # --------------------------------------------------------

    router_words = (
        "router",
        "gateway",
        "mikrotik",
        "ubiquiti",
        "unifi",
        "cisco",
        "juniper",
        "openwrt",
        "pfsense",
        "opnsense",
        "fortigate",
        "tplink",
        "tp-link",
        "netgear",
        "asus",
        "keenetic"
    )

    if any(
        word in fingerprint
        for word in router_words
    ):

        return "router"

    # --------------------------------------------------------
    # TV / MEDIA
    # --------------------------------------------------------

    tv_words = (
        "tv",
        "smart-tv",
        "samsung",
        "lgwebos",
        "webos",
        "bravia",
        "androidtv",
        "chromecast",
        "firetv",
        "roku",
        "hisense",
        "philips"
    )

    if any(
        word in fingerprint
        for word in tv_words
    ):

        return "tv"

    # --------------------------------------------------------
    # PHONE / MOBILE
    # --------------------------------------------------------

    phone_words = (
        "iphone",
        "android",
        "pixel",
        "galaxy",
        "oneplus",
        "xiaomi",
        "redmi",
        "huawei",
        "honor",
        "mobile",
        "phone"
    )

    if any(
        word in fingerprint
        for word in phone_words
    ):

        return "phone"

    # --------------------------------------------------------
    # SERVER
    # --------------------------------------------------------

    server_words = (
        "server",
        "srv",
        "nas",
        "storage",
        "proxmox",
        "docker",
        "kubernetes",
        "k8s",
        "esxi",
        "vmware",
        "linux-server"
    )

    if any(
        word in fingerprint
        for word in server_words
    ):

        return "server"

    if ports.intersection({
        22,
        3389,
        5985,
        5986
    }) and ports.intersection({
        80,
        443,
        8080,
        8443
    }):

        return "server"

    # --------------------------------------------------------
    # COMPUTER
    # --------------------------------------------------------

    computer_words = (
        "desktop",
        "workstation",
        "pc",
        "computer",
        "windows",
        "ubuntu",
        "debian",
        "fedora",
        "arch",
        "mint",
        "linux"
    )

    if any(
        word in fingerprint
        for word in computer_words
    ):

        return "computer"

    # --------------------------------------------------------
    # IOT
    # --------------------------------------------------------

    iot_words = (
        "iot",
        "esp32",
        "esp8266",
        "homeassistant",
        "tasmota",
        "sonoff",
        "shelly",
        "tuya",
        "zigbee",
        "sensor",
        "plug",
        "switch",
        "bulb"
    )

    if any(
        word in fingerprint
        for word in iot_words
    ):

        return "iot"

    # --------------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------------

    return "unknown"


# ============================================================
# SERVICE SCAN
# ============================================================

def scan_services(
    ip,
    services=None,
    cancel_event=None
):

    """
    Osnovni servis fingerprinting.

    Ne koristi privileged Nmap.
    Radi TCP connect scan.
    """

    services = {

        22: "SSH",

        23: "Telnet",

        53: "DNS",

        80: "HTTP",

        81: "HTTP",

        443: "HTTPS",

        445: "SMB",

        515: "LPD",

        554: "RTSP",

        631: "IPP",

        1883: "MQTT",

        3389: "RDP",

        5000: "HTTP",

        5001: "HTTPS",

        8000: "HTTP",

        8080: "HTTP",

        8443: "HTTPS",

        8554: "RTSP",

        9100: "JetDirect",

        5985: "WinRM",

        5986: "WinRM SSL"

    }

    found = []

    for port, name in services.items():

        if (
            cancel_event
            and cancel_event.is_set()
        ):

            return found

        if check_port(
            ip,
            port
        ):

            found.append({

                "service": name,

                "port": port

            })

    return found


# ============================================================
# HOST SCAN
# ============================================================

def scan_host(
    ip,
    services=None,
    cancel_event=None
):

    if (
        cancel_event
        and cancel_event.is_set()
    ):

        return None

    ip = str(ip)

    if not ping_host(ip):

        return None

    if (
        cancel_event
        and cancel_event.is_set()
    ):

        return None

    found_services = scan_services(
        ip,
        cancel_event=cancel_event
    )

    if (
        cancel_event
        and cancel_event.is_set()
    ):

        return None

    hostname = resolve_hostname(
        ip
    )

    neighbor = get_neighbor_info(
        ip
    )

    open_ports = [
        item["port"]
        for item in found_services
    ]

    http_identity = None

    http_ports = [
        80,
        81,
        443,
        5000,
        5001,
        8000,
        8080,
        8443
    ]

    for port in open_ports:

        if port in http_ports:

            http_identity = detect_http_identity(
                ip,
                port
            )

            if (
                http_identity.get("server")
                or http_identity.get("headers")
            ):

                break

    device_type = classify_device(

        host=ip,

        hostname=hostname,

        open_ports=open_ports,

        services=found_services,

        http_identity=http_identity

    )

    display_name = (
        hostname
        if hostname
        else f"Discovered-{ip}"
    )

    return {

        "type": device_type,

        "name": display_name,

        "host": ip,

        "hostname": hostname,

        "mac": neighbor.get(
            "mac"
        ),

        "interface": neighbor.get(
            "interface"
        ),

        "os": "unknown",

        "port": (
            found_services[0]["port"]
            if found_services
            else None
        ),

        "ports": open_ports,

        "services": found_services,

        "status": "alive",

        "group": "network"

    }


# ============================================================
# NETWORK DISCOVERY
# ============================================================

def discover_network_hosts(
    network,
    progress_callback=None,
    cancel_event=None
):

    """
    Network discovery.

    Ping + TCP service detection +
    hostname + Linux neighbor information +
    basic device fingerprinting.

    Supports cancellation through
    threading.Event().

    IMPORTANT:

    This is FAST DISCOVERY.

    Nmap is NOT called here.

    Nmap deep scan is performed only
    by nmap_scan() for one selected host.
    """

    hosts = []

    net = ipaddress.ip_network(
        network,
        strict=False
    )

    addresses = list(
        net.hosts()
    )

    total = len(
        addresses
    )

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
                    None,
                    cancel_event
                )
            )

        for future in as_completed(
            futures
        ):

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


# ============================================================
# NMAP DEEP SCAN
# ============================================================

def nmap_scan(
    host,
    timeout=60
):

    """
    Comprehensive scan of ONE already discovered host.

    FAST DISCOVERY never calls this function.

    This function is called only after the user opens
    Details and explicitly requests DEEP SCAN.

    Uses:

        -Pn
        -sT
        -sV
        --open
        -T4

    This means:

        no privileged/raw packet scan required
        TCP connect scan
        service/version detection
        only open ports returned
    """

    host = str(
        host
    ).strip()

    if not host:

        raise ValueError(
            "Host is empty"
        )

    # --------------------------------------------------------
    # VALIDATE HOST
    # --------------------------------------------------------

    try:

        ipaddress.ip_address(
            host
        )

    except ValueError:

        try:

            socket.gethostbyname(
                host
            )

        except Exception:

            raise ValueError(
                f"Invalid host: {host}"
            )

    # --------------------------------------------------------
    # FIND NMAP
    # --------------------------------------------------------

    nmap_binary = shutil.which(
        "nmap"
    )

    if not nmap_binary:

        raise RuntimeError(
            "Nmap is not installed"
        )

    # --------------------------------------------------------
    # COMMAND
    # --------------------------------------------------------

    command = [

        nmap_binary,

        "-Pn",

        "-sT",

        "-sV",

        "--open",

        "-T4",

        host

    ]

    print(
        "NMAP DEEP SCAN START:",
        host
    )

    print(
        "NMAP COMMAND:",
        " ".join(command)
    )

    # --------------------------------------------------------
    # EXECUTE
    # --------------------------------------------------------

    try:

        result = subprocess.run(

            command,

            capture_output=True,

            text=True,

            timeout=timeout

        )

    except subprocess.TimeoutExpired:

        raise RuntimeError(
            f"Nmap scan timeout for {host}"
        )

    except Exception as e:

        raise RuntimeError(
            f"Nmap execution failed: {e}"
        )

    stdout = (
        result.stdout
        or ""
    )

    stderr = (
        result.stderr
        or ""
    )

    if result.returncode != 0:

        error = (
            stderr.strip()
            or stdout.strip()
            or "Unknown nmap error"
        )

        raise RuntimeError(
            error
        )

    # --------------------------------------------------------
    # PARSE SERVICES
    # --------------------------------------------------------

    services = []

    ports = []

    for line in stdout.splitlines():

        line = line.strip()

        match = re.match(
            r"^(\d+)/tcp\s+(\S+)\s*(.*)$",
            line
        )

        if not match:

            continue

        port = int(
            match.group(1)
        )

        state = match.group(2)

        service_text = (
            match.group(3).strip()
        )

        if state != "open":

            continue

        service_name = (
            service_text
            or "unknown"
        )

        version = None

        # ----------------------------------------------------
        # NMAP SERVICE FORMAT
        #
        # Examples:
        #
        # 22/tcp open ssh OpenSSH 9.6
        # 80/tcp open http nginx 1.24
        # ----------------------------------------------------

        parts = service_text.split(
            None,
            1
        )

        if parts:

            service_name = parts[0]

            if len(parts) > 1:

                version = parts[1].strip()

        service = {

            "service": service_name,

            "port": port,

            "protocol": "tcp"

        }

        if version:

            service[
                "version"
            ] = version

        services.append(
            service
        )

        ports.append(
            port
        )

    # --------------------------------------------------------
    # HOSTNAME
    # --------------------------------------------------------

    hostname = None

    host_match = re.search(
        r"Nmap scan report for\s+(.+)",
        stdout
    )

    if host_match:

        report_name = (
            host_match.group(1).strip()
        )

        # Format:
        #
        # hostname (192.168.2.111)
        #
        hostname_match = re.match(
            r"^(.+?)\s+\(([^)]+)\)$",
            report_name
        )

        if hostname_match:

            candidate = (
                hostname_match.group(1).strip()
            )

            candidate_ip = (
                hostname_match.group(2).strip()
            )

            if candidate_ip == host:

                hostname = candidate

        else:

            if report_name != host:

                hostname = report_name

    # --------------------------------------------------------
    # OS DETECTION
    #
    # Note:
    #
    # We deliberately do NOT use -O here because it usually
    # requires privileged/raw packet access.
    #
    # Service/version fingerprinting is still performed.
    # --------------------------------------------------------

    detected_os = "unknown"

    os_match = re.search(
        r"OS details:\s*(.+)",
        stdout
    )

    if os_match:

        detected_os = (
            os_match.group(1).strip()
        )

    else:

        aggressive_os = re.search(
            r"Aggressive OS guesses:\s*(.+)",
            stdout
        )

        if aggressive_os:

            detected_os = (
                aggressive_os.group(1).strip()
            )

    # --------------------------------------------------------
    # MAC ADDRESS
    # --------------------------------------------------------

    mac = None

    mac_match = re.search(
        r"MAC Address:\s*([0-9A-Fa-f:]{17})",
        stdout
    )

    if mac_match:

        mac = (
            mac_match.group(1).lower()
        )

    # --------------------------------------------------------
    # VENDOR
    # --------------------------------------------------------

    vendor = None

    if mac_match:

        mac_line = mac_match.group(0)

        vendor_match = re.search(
            r"\(([^\)]+)\)\s*$",
            mac_line
        )

        if vendor_match:

            vendor = (
                vendor_match.group(1).strip()
            )

    # --------------------------------------------------------
    # HTTP IDENTITY
    # --------------------------------------------------------

    http_identity = None

    http_ports = {

        80,
        81,
        443,
        5000,
        5001,
        8000,
        8080,
        8443

    }

    for port in ports:

        if port not in http_ports:

            continue

        try:

            identity = detect_http_identity(
                host,
                port
            )

            if identity:

                http_identity = identity

                if (
                    identity.get("server")
                    or identity.get("headers")
                ):

                    break

        except Exception:

            pass

    # --------------------------------------------------------
    # DEVICE CLASSIFICATION
    # --------------------------------------------------------

    device_type = classify_device(

        host=host,

        hostname=hostname,

        open_ports=ports,

        services=services,

        http_identity=http_identity

    )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    result_data = {

        "host": host,

        "hostname": hostname,

        "mac": mac,

        "vendor": vendor,

        "ports": ports,

        "services": services,

        "os": detected_os,

        "type": device_type,

        "device_type": device_type,

        "nmap_scan": True,

        "nmap_scan_status": "completed",

        "nmap_output": stdout

    }

    if http_identity:

        result_data[
            "http_identity"
        ] = http_identity

    print(
        "NMAP DEEP SCAN COMPLETE:",
        host
    )

    print(
        "NMAP PORTS:",
        ports
    )

    print(
        "NMAP OS:",
        detected_os
    )

    print(
        "NMAP TYPE:",
        device_type
    )

    return result_data