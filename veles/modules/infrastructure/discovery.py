"""
Veles Infrastructure Discovery

Prikupljanje osnovnih podataka
lokalnog sistema.
"""


import platform
import socket
import shutil
import os

from .models import Server



def get_hostname():

    return socket.gethostname()



def get_ip():

    try:

        hostname = socket.gethostname()

        return socket.gethostbyname(hostname)

    except Exception:

        return "unknown"



def get_disk_usage():

    total, used, free = shutil.disk_usage("/")

    return {

        "total_gb":
            round(total / (1024**3), 2),

        "used_gb":
            round(used / (1024**3), 2),

        "free_gb":
            round(free / (1024**3), 2),

    }



def discover_local_server():

    server = Server(

        name="Veles Core",

        hostname=get_hostname(),

        ip=get_ip(),

        os=platform.platform()

    )


    server.touch()


    return server