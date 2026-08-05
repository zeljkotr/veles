"""
Veles Infrastructure Discovery

Prikupljanje osnovnih podataka
lokalnog sistema.
"""


import platform
import socket
import shutil
import os
import time


from .models import Server





def get_hostname():

    return socket.gethostname()





def get_ip():

    try:

        hostname = socket.gethostname()

        return socket.gethostbyname(hostname)

    except Exception:

        return "unknown"






def get_cpu():

    try:

        with open("/proc/loadavg", "r") as f:

            load = f.read().split()[0]

        return load


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

            "total_gb":
                round(total, 2),


            "used_gb":
                round(used, 2),


            "free_gb":
                round(available, 2)

        }


    except Exception:

        return {

            "total_gb":0,

            "used_gb":0,

            "free_gb":0

        }






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







def get_uptime():

    try:

        with open("/proc/uptime","r") as f:

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