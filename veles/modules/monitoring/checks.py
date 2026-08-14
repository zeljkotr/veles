"""
VELES Monitoring Checks

Health checks:
- ping
- port
- http
"""

import socket
import subprocess
import time

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_PING_TIMEOUT = 3
DEFAULT_PORT_TIMEOUT = 3
DEFAULT_HTTP_TIMEOUT = 5


def check_ping(
    host: str,
    timeout: int = DEFAULT_PING_TIMEOUT
):
    """
    Check whether a host is reachable.

    Uses the system ping command so this is an actual
    network reachability test rather than DNS resolution.
    """

    if not host:
        return {
            "status": "unknown",
            "response_time_ms": None,
            "message": "Host is not configured"
        }

    start = time.perf_counter()

    try:

        result = subprocess.run(
            [
                "ping",
                "-c",
                "1",
                "-W",
                str(timeout),
                str(host)
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout + 1,
            check=False
        )

        elapsed = (
            time.perf_counter() - start
        ) * 1000

        if result.returncode == 0:

            return {
                "status": "online",
                "response_time_ms": round(
                    elapsed,
                    2
                ),
                "message": "Host reachable"
            }

        return {
            "status": "offline",
            "response_time_ms": round(
                elapsed,
                2
            ),
            "message": "Host unreachable"
        }

    except subprocess.TimeoutExpired:

        return {
            "status": "offline",
            "response_time_ms": None,
            "message": "Ping timeout"
        }

    except FileNotFoundError:

        return {
            "status": "unknown",
            "response_time_ms": None,
            "message": "ping command not available"
        }

    except Exception as exc:

        return {
            "status": "unknown",
            "response_time_ms": None,
            "message": str(exc)
        }


def check_port(
    host: str,
    port: int,
    timeout: int = DEFAULT_PORT_TIMEOUT
):
    """
    Check TCP port availability.
    """

    if not host:
        return {
            "status": "unknown",
            "response_time_ms": None,
            "message": "Host is not configured"
        }

    if not port:

        return {
            "status": "unknown",
            "response_time_ms": None,
            "message": "Port is not configured"
        }

    start = time.perf_counter()

    sock = None

    try:

        sock = socket.create_connection(
            (
                str(host),
                int(port)
            ),
            timeout=timeout
        )

        elapsed = (
            time.perf_counter() - start
        ) * 1000

        return {
            "status": "online",
            "response_time_ms": round(
                elapsed,
                2
            ),
            "message": f"Port {port} open"
        }

    except socket.timeout:

        return {
            "status": "offline",
            "response_time_ms": None,
            "message": f"Port {port} connection timeout"
        }

    except OSError as exc:

        return {
            "status": "offline",
            "response_time_ms": None,
            "message": str(exc)
        }

    except Exception as exc:

        return {
            "status": "unknown",
            "response_time_ms": None,
            "message": str(exc)
        }

    finally:

        if sock is not None:

            try:
                sock.close()
            except Exception:
                pass


def check_http(
    url: str,
    timeout: int = DEFAULT_HTTP_TIMEOUT
):
    """
    Check HTTP or HTTPS availability.

    HTTP 2xx/3xx and HTTP error responses such as 404
    still prove that the HTTP service is reachable.
    """

    if not url:

        return {
            "status": "unknown",
            "response_time_ms": None,
            "message": "URL is not configured"
        }

    start = time.perf_counter()

    try:

        request = Request(
            url,
            method="GET"
        )

        response = urlopen(
            request,
            timeout=timeout
        )

        elapsed = (
            time.perf_counter() - start
        ) * 1000

        code = getattr(
            response,
            "status",
            response.getcode()
        )

        try:
            response.close()
        except Exception:
            pass

        return {
            "status": "online",
            "response_time_ms": round(
                elapsed,
                2
            ),
            "message": f"HTTP {code}"
        }

    except HTTPError as exc:

        elapsed = (
            time.perf_counter() - start
        ) * 1000

        return {
            "status": "online",
            "response_time_ms": round(
                elapsed,
                2
            ),
            "message": f"HTTP {exc.code}"
        }

    except URLError as exc:

        return {
            "status": "offline",
            "response_time_ms": None,
            "message": str(exc.reason)
        }

    except TimeoutError:

        return {
            "status": "offline",
            "response_time_ms": None,
            "message": "HTTP request timeout"
        }

    except Exception as exc:

        return {
            "status": "unknown",
            "response_time_ms": None,
            "message": str(exc)
        }


def run_check(
    check_type: str,
    target: dict
):
    """
    Universal monitoring dispatcher.
    """

    if not isinstance(target, dict):

        return {
            "status": "unknown",
            "response_time_ms": None,
            "message": "Invalid monitoring target"
        }

    check_type = str(
        check_type or ""
    ).strip().lower()

    try:

        if check_type == "ping":

            return check_ping(
                target.get("host")
            )

        if check_type == "port":

            return check_port(
                target.get("host"),
                target.get("port")
            )

        if check_type == "http":

            return check_http(
                target.get("url")
            )

        return {
            "status": "unknown",
            "response_time_ms": None,
            "message": (
                f"Unknown check: {check_type}"
            )
        }

    except Exception as exc:

        return {
            "status": "unknown",
            "response_time_ms": None,
            "message": str(exc)
        }