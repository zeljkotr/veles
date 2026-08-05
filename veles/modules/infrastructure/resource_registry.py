"""
Veles Infrastructure Resource Registry

Centralni registar svih infrastrukturnih resursa.
"""

import json
from pathlib import Path


DATABASE_FILE = (
    Path(__file__)
    .resolve()
    .parents[2]
    / "database"
    / "resources.json"
)



class ResourceRegistry:


    def __init__(self):

        self.resources = {

            "servers": [],
            "containers": [],
            "agents": [],
            "devices": [],
            "cloud": []

        }

        self.load()





    def load(self):

        if not DATABASE_FILE.exists():

            self.save()


        with open(
            DATABASE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            self.resources = json.load(file)







    def save(self):

        DATABASE_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )


        with open(
            DATABASE_FILE,
            "w",
            encoding="utf-8"
        ) as file:


            json.dump(

                self.resources,

                file,

                indent=4,

                ensure_ascii=False

            )







    def add_resource(self, resource):


        resource_type = resource.get(
            "type",
            "server"
        )


        group = {


            "server": "servers",

            "container": "containers",

            "agent": "agents",

            "device": "devices",

            "cloud": "cloud"


        }.get(
            resource_type,
            "servers"
        )



        self.resources[group].append(
            resource
        )


        self.save()


        return resource






    def get_resources(self, group=None):


        if group:

            return self.resources.get(
                group,
                []
            )


        return self.resources