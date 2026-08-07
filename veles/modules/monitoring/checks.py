"""
VELES Monitoring Checks

Basic health checks:
- ping
- port
- http
"""

import socket
import time

from urllib.request import urlopen
from urllib.error import URLError



def check_ping(host: str, timeout: int = 3):
    """
    Basic network reachability check.
    """

    start = time.time()

    try:

        socket.gethostbyname(host)

        response = (
            time.time() - start
        ) * 1000


        return {
            "status": "online",
            "response_time_ms": round(
                response,
                2
            ),
            "message": "Host reachable"
        }


    except Exception as e:

        return {
            "status": "offline",
            "response_time_ms": None,
            "message": str(e)
        }



def check_port(
    host: str,
    port: int,
    timeout: int = 3
):
    """
    TCP port availability check.
    """

    start = time.time()

    try:

        sock = socket.create_connection(
            (
                host,
                int(port)
            ),
            timeout=timeout
        )

        sock.close()


        response = (
            time.time() - start
        ) * 1000


        return {
            "status": "online",
            "response_time_ms": round(
                response,
                2
            ),
            "message": f"Port {port} open"
        }


    except Exception as e:

        return {
            "status": "offline",
            "response_time_ms": None,
            "message": str(e)
        }



def check_http(
    url: str,
    timeout: int = 5
):
    """
    HTTP availability check.
    """

    start = time.time()


    try:

        response = urlopen(
            url,
            timeout=timeout
        )


        code = response.status


        elapsed = (
            time.time() - start
        ) * 1000


        return {
            "status": "online",
            "response_time_ms": round(
                elapsed,
                2
            ),
            "message": f"HTTP {code}"
        }


    except URLError as e:

        return {
            "status": "offline",
            "response_time_ms": None,
            "message": str(e)
        }



def run_check(
    check_type: str,
    target: dict
):
    """
    Universal monitoring dispatcher.
    """

    if check_type == "ping":

        return check_ping(
            target["host"]
        )


    if check_type == "port":

        return check_port(
            target["host"],
            target.get(
                "port",
                0
            )
        )


    if check_type == "http":

        return check_http(
            target["url"]
        )


    return {
        "status": "unknown",
        "message": (
            f"Unknown check: {check_type}"
        )
    }