"""
Veles Delivery Service

Prikuplja trenutno stanje
delivery sistema Veles.
"""

from veles.modules.infrastructure.resource_registry import ResourceRegistry


class DeliveryService:

    def __init__(self):

        self.resource_registry = ResourceRegistry()

        self.loaded = False

        self.pipelines = []


    def get_targets(self):

        resources = self.resource_registry.get_resources()

        target_types = {
            "server",
            "container",
            "agent"
        }

        return [
            resource
            for resource in resources
            if resource.get("type") in target_types
        ]


    def get_pipelines(self):

        return self.pipelines


    def get_status(self):

        targets = self.get_targets()

        pipelines = self.get_pipelines()

        return {

            "status": "ready",

            "pipelines": len(pipelines),

            "deployments": 0,

            "targets": len(targets),

            "target_list": targets,

            "pipeline_list": pipelines

        }


delivery = DeliveryService()