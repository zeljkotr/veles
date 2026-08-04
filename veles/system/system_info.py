"""
Veles System Information Module

Prikuplja osnovne Linux sistemske podatke.

Koristi:
- platform
- psutil
- shutil
- os
- proc filesystem
"""


import platform
import shutil
import socket
import time

import psutil





def get_cpu_model():

    """
    Čita pravi naziv procesora iz Linux sistema.
    """

    try:

        with open(
            "/proc/cpuinfo",
            "r",
            encoding="utf-8"
        ) as file:


            for line in file:


                if "model name" in line:


                    return (
                        line
                        .split(":")[1]
                        .strip()
                    )



    except Exception:

        pass



    return (
        platform.processor()
        or "Nepoznat CPU"
    )







def get_uptime():

    """
    Vraća vreme rada sistema.
    """

    boot_time = psutil.boot_time()

    uptime_seconds = int(
        time.time() - boot_time
    )


    days = uptime_seconds // 86400

    hours = (
        uptime_seconds % 86400
    ) // 3600

    minutes = (
        uptime_seconds % 3600
    ) // 60


    return (
        f"{days} dana "
        f"{hours} sati "
        f"{minutes} minuta"
    )







def get_disk_info():

    disk = shutil.disk_usage("/")


    total = disk.total / (
        1024 ** 3
    )

    used = disk.used / (
        1024 ** 3
    )

    free = disk.free / (
        1024 ** 3
    )


    percent = (
        disk.used / disk.total
    ) * 100



    return {

        "total": round(
            total,
            2
        ),

        "used": round(
            used,
            2
        ),

        "free": round(
            free,
            2
        ),

        "percent": round(
            percent,
            1
        )

    }







def get_memory_info():

    memory = psutil.virtual_memory()


    return {

        "total": round(
            memory.total / (1024 ** 3),
            2
        ),

        "used": round(
            memory.used / (1024 ** 3),
            2
        ),

        "available": round(
            memory.available / (1024 ** 3),
            2
        ),

        "percent": memory.percent

    }







def get_cpu_info():


    return {

        "model": get_cpu_model(),


        "cores": psutil.cpu_count(
            logical=False
        ),


        "threads": psutil.cpu_count(
            logical=True
        ),


        "usage": psutil.cpu_percent(
            interval=1
        )

    }







def get_system_info():


    return {


        "hostname": socket.gethostname(),


        "os": platform.system()
        + " "
        + platform.release(),


        "kernel": platform.release(),


        "architecture": platform.machine(),


        "cpu": get_cpu_info(),


        "memory": get_memory_info(),


        "disk": get_disk_info(),


        "uptime": get_uptime()


    }