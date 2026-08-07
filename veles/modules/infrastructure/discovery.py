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
            total / (1024**3),
            2
        ),

        "used_gb": round(
            used / (1024**3),
            2
        ),

        "free_gb": round(
            free / (1024**3),
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



def discover_network_targets():

    """
    Pronalazi mrežne targete.

    Ne skenira.
    Ne dodaje resurse.
    """

    targets = []


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

        return targets



    for line in result.splitlines():

        parts = line.split()


        if len(parts) < 4:

            continue


        interface = parts[1]

        address = parts[3]


        if interface == "lo":

            continue


        if interface.startswith("docker"):

            continue


        try:

            ip_interface = ipaddress.ip_interface(
                address
            )


            targets.append(

                {

                    "interface": interface,

                    "address": str(ip_interface),

                    "network": str(
                        ip_interface.network
                    )

                }

            )


        except ValueError:

            continue



    return targets



def check_port(host, port, timeout=0.2):

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



def ping_host(ip, timeout=1):

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



def scan_host(ip, services):

    ip = str(ip)

    found_services = []


    if not ping_host(ip):

        return None



    for port, name in services.items():

        if check_port(
            ip,
            port
        ):

            found_services.append(

                {

                    "service": name,

                    "port": port

                }

            )



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



def discover_network_hosts(network, progress_callback=None):

    """
    Network discovery.

    Ping + service detection.
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

            futures.append(

                executor.submit(

                    scan_host,

                    ip,

                    services

                )

            )



        for future in as_completed(futures):

            result = future.result()

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



    if progress_callback:

        progress_callback({

            "running": False,

            "network": network,

            "total": total,

            "checked": checked,

            "found": len(hosts),

            "results": hosts

        })


    return hosts