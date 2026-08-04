"""
Veles Infrastructure Inventory

Sakuplja i čuva informacije
o infrastrukturi.
"""


from .models import (
    Server,
    Device,
    Agent,
)



class InfrastructureInventory:


    def __init__(self):

        self.servers = []

        self.devices = []

        self.agents = []



    def add_server(
        self,
        server: Server
    ):

        self.servers.append(server)



    def add_device(
        self,
        device: Device
    ):

        self.devices.append(device)



    def add_agent(
        self,
        agent: Agent
    ):

        self.agents.append(agent)



    def get_servers(self):

        return self.servers



    def get_devices(self):

        return self.devices



    def get_agents(self):

        return self.agents



    def summary(self):

        return {

            "servers":
                len(self.servers),

            "devices":
                len(self.devices),

            "agents":
                len(self.agents),

        }



# globalni inventar Velesa

inventory = InfrastructureInventory()