"""
Veles Infrastructure Service

Glavni servis infrastrukture.

Povezuje:

- local discovery
- network discovery
- resource registry (PostgreSQL)
- inventory
"""


from .inventory import inventory

from .discovery import (
    discover_local_server,
    discover_network_hosts
)

from .resource_registry import ResourceRegistry

from .models import Server, LOCAL_SERVER



class InfrastructureService:


    def __init__(self):

        self.inventory = inventory

        self.resource_registry = ResourceRegistry()

        self.loaded = False



    def _add_if_missing(self, server):

        """
        Sprečava duplikate u inventaru.
        """


        for item in self.inventory.get_servers():


            if item.ip == server.ip:

                return


            if (
                item.name == server.name
                and item.hostname == server.hostname
            ):

                return


        self.inventory.add_server(server)



    def discover(self):

        """
        Discovery lokalnog servera
        i mrežnih resursa.

        Discovery samo pronalazi.
        Ne registruje automatski.
        """


        server = discover_local_server()


        self._add_if_missing(
            server
        )


        hosts = discover_network_hosts()


        return {

            "local": server,

            "discovered": hosts

        }



    def initialize(self):

        """
        Učitavanje početnog stanja.
        """


        if self.loaded:

            return


        self._add_if_missing(
            LOCAL_SERVER
        )


        self.loaded = True



    def add_resource(self, resource):

        """
        Ručno dodavanje potvrđenog resursa.
        """

        return self.resource_registry.add_resource(
            resource
        )



    def get_registered_server(self, server_id):

        resources = self.resource_registry.get_resources()


        for resource in resources:


            if str(resource["id"]) == str(server_id):

                return resource


        return None



    def get_resources(self, group=None):

        return self.resource_registry.get_resources(
            group
        )



    def get_status(self):

        """
        Status infrastrukture.

        UI očekuje Server objekte
        iz inventory-ja.
        """


        self.initialize()


        local_server = discover_local_server()


        self._add_if_missing(
            local_server
        )


        resources = self.resource_registry.get_resources()



        grouped_resources = {


            "servers": [],

            "containers": [],

            "agents": [],

            "devices": [],

            "cloud": []

        }



        mapping = {


            "server": "servers",

            "container": "containers",

            "agent": "agents",

            "device": "devices",

            "cloud": "cloud"

        }



        for resource in resources:


            group = mapping.get(

                resource.get("type"),

                "servers"

            )


            grouped_resources[group].append(
                resource
            )



        return {


            "inventory": self.inventory.summary(),


            "servers": self.inventory.get_servers(),


            "devices": self.inventory.get_devices(),


            "agents": self.inventory.get_agents(),


            "resources": grouped_resources

        }



# Globalni servis

infrastructure = InfrastructureService()