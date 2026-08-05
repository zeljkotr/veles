"""
Veles Infrastructure Server Registry

Upravljanje registrovanim serverima.
"""

import json
from pathlib import Path


DATABASE_FILE = (
    Path(__file__)
    .resolve()
    .parents[2]
    / "database"
    / "servers.json"
)


class ServerRegistry:
    """
    Registry svih servera kojima Veles upravlja.
    """

    def __init__(self):
        self.servers = []
        self.load()


    def load(self):
        """
        Učitavanje servera iz baze.
        """

        if not DATABASE_FILE.exists():
            self.save()

        with open(
            DATABASE_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        self.servers = data.get(
            "servers",
            []
        )


    def save(self):
        """
        Čuvanje servera.
        """

        with open(
            DATABASE_FILE,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                {
                    "servers": self.servers
                },
                file,
                indent=4,
                ensure_ascii=False
            )


    def list_servers(self):
        """
        Vraća sve registrovane servere.
        """

        return self.servers


    def add_server(self, server):
        """
        Dodaje novi server.
        """

        self.servers.append(server)
        self.save()

        return server


    def get_server(self, server_id):
        """
        Pronalazi server po ID-u.
        """

        for server in self.servers:
            if server.get("id") == server_id:
                return server

        return None


    def remove_server(self, server_id):
        """
        Briše server iz registry-ja.
        """

        self.servers = [
            server
            for server in self.servers
            if server.get("id") != server_id
        ]

        self.save()