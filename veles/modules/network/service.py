"""
Veles Network Service

Prikuplja trenutno stanje mreže
lokalnog Veles sistema.
"""

import socket
import subprocess


class NetworkService:

    def __init__(self):
        self.loaded = False

    def _run(self, command):

        try:

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                return result.stdout.strip()

            return ""

        except Exception as e:

            print(
                "NETWORK ERROR:",
                e
            )

            return ""

    def get_hostname(self):

        try:

            return socket.gethostname()

        except Exception:

            return "unknown"

    def get_interfaces(self):

        output = self._run(
            [
                "ip",
                "-o",
                "-4",
                "addr"
            ]
        )

        interfaces = []

        for line in output.splitlines():

            parts = line.split()

            if len(parts) < 4:
                continue

            interface = parts[1]
            address = parts[3]

            interfaces.append(
                {
                    "interface": interface,
                    "address": address
                }
            )

        return interfaces

    def get_routes(self):

        output = self._run(
            [
                "ip",
                "route"
            ]
        )

        return output.splitlines()

    def get_dns(self):

        output = self._run(
            [
                "resolvectl",
                "status"
            ]
        )

        return output

    def get_status(self):

        return {

            "hostname":
                self.get_hostname(),

            "interfaces":
                self.get_interfaces(),

            "routes":
                self.get_routes(),

            "dns":
                self.get_dns()

        }


network = NetworkService()
