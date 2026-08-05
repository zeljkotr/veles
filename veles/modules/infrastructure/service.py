"""
Veles Infrastructure Service

Glavni servis infrastrukture.

Povezuje:
- local discovery
- server registry
- resource registry
- inventory
"""


from .inventory import inventory

from .discovery import discover_local_server

from .server_registry import ServerRegistry

from .resource_registry import ResourceRegistry

from .models import Server, LOCAL_SERVER





class InfrastructureService:


    def __init__(self):

        self.inventory = inventory

        self.registry = ServerRegistry()

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



        self.inventory.add_server(
            server
        )







    def _load_registry_servers(self):

        """
        Učitava registrovane servere
        iz servers.json
        """


        servers = self.registry.list_servers()



        for item in servers:


            server = Server(

                name=item.get(
                    "name",
                    "Unknown"
                ),


                hostname=item.get(
                    "host",
                    "unknown"
                ),


                ip=item.get(
                    "host",
                    "unknown"
                ),


                os="unknown",


                status=item.get(
                    "status",
                    "registered"
                )

            )


            self._add_if_missing(
                server
            )









    def discover(self):

        """
        Discovery lokalnog Veles servera.
        """


        server = discover_local_server()


        self._add_if_missing(
            server
        )


        return server







    def initialize(self):

        """
        Učitavanje početnog stanja infrastrukture.
        """


        if self.loaded:

            return



        self._add_if_missing(
            LOCAL_SERVER
        )



        self._load_registry_servers()



        self.loaded = True







    def add_resource(self, resource):

        """
        Dodavanje resursa u Infrastructure Registry.
        """

        return self.resource_registry.add_resource(
            resource
        )









    def get_registered_server(self, server_id):

        """
        Vraća server iz Server Registry baze.
        """


        return self.registry.get_server(
            server_id
        )









    def get_resources(self, group=None):

        """
        Vraća Infrastructure resurse.
        """


        return self.resource_registry.get_resources(
            group
        )









    def get_status(self):


        self.initialize()



        return {



            "inventory":

                self.inventory.summary(),




            "servers":

                self.inventory.get_servers(),




            "devices":

                self.inventory.get_devices(),




            "agents":

                self.inventory.get_agents(),


            "resources":

                self.resource_registry.get_resources()


        }








# globalni servis


infrastructure = InfrastructureService()