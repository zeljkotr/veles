"""
Veles Infrastructure Service

Glavni servis infrastrukture.
Povezuje discovery i inventory.
"""


from .inventory import inventory

from .discovery import discover_local_server



class InfrastructureService:


    def __init__(self):

        self.inventory = inventory



    def discover(self):

        server = discover_local_server()

        self.inventory.add_server(server)

        return server



    def get_status(self):

        return {

            "inventory":
                self.inventory.summary(),

            "servers":
                self.inventory.get_servers(),

            "devices":
                self.inventory.get_devices(),

            "agents":
                self.inventory.get_agents(),

        }



# globalni servis

infrastructure = InfrastructureService()