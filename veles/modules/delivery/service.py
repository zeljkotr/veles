"""
Veles Delivery Service

Prikuplja trenutno stanje
delivery sistema Veles.
"""

class DeliveryService:

    def __init__(self):
        self.loaded = False

    def get_status(self):

        return {

            "status": "ready",

            "pipelines": 0,

            "deployments": 0,

            "targets": 0

        }


delivery = DeliveryService()