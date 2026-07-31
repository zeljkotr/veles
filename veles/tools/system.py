import platform
import shutil
import psutil


def system_info(context=None):

    cpu = psutil.cpu_percent(interval=1)

    memory = psutil.virtual_memory()

    disk = shutil.disk_usage("/")


    return {

        "hostname": platform.node(),

        "os": platform.system(),

        "cpu_usage": f"{cpu}%",

        "memory_total": f"{round(memory.total / (1024**3), 2)} GB",

        "memory_used": f"{round(memory.used / (1024**3), 2)} GB",

        "memory_percent": f"{memory.percent}%",

        "disk_total": f"{round(disk.total / (1024**3), 2)} GB",

        "disk_used": f"{round(disk.used / (1024**3), 2)} GB",

        "disk_free": f"{round(disk.free / (1024**3), 2)} GB"

    }