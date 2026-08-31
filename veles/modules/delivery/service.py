"""
VELES Delivery Service

Prikuplja i upravlja stanjem
delivery sistema VELES.
"""

from veles.database.connection import get_session
from veles.database.models import Pipeline
from veles.modules.infrastructure.resource_registry import ResourceRegistry


class DeliveryService:

    def __init__(self):

        self.resource_registry = ResourceRegistry()

        self.loaded = False

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

        session = get_session()

        try:

            pipelines = (
                session.query(Pipeline)
                .order_by(Pipeline.id)
                .all()
            )

            return [
                {
                    "id": pipeline.id,
                    "name": pipeline.name,
                    "description": pipeline.description,
                    "status": pipeline.status,
                    "trigger": pipeline.trigger,
                    "target_selector": pipeline.target_selector,
                    "configuration": pipeline.configuration,
                    "created_at": (
                        pipeline.created_at.isoformat()
                        if pipeline.created_at
                        else None
                    ),
                    "updated_at": (
                        pipeline.updated_at.isoformat()
                        if pipeline.updated_at
                        else None
                    ),
                    "steps": [
                        {
                            "id": step.id,
                            "position": step.position,
                            "name": step.name,
                            "type": step.type,
                            "configuration": step.configuration
                        }
                        for step in pipeline.steps
                    ]
                }
                for pipeline in pipelines
            ]

        finally:

            session.close()

    def get_pipeline(self, pipeline_id):

        session = get_session()

        try:

            pipeline = (
                session.query(Pipeline)
                .filter(Pipeline.id == pipeline_id)
                .first()
            )

            if pipeline is None:
                return None

            return {
                "id": pipeline.id,
                "name": pipeline.name,
                "description": pipeline.description,
                "status": pipeline.status,
                "trigger": pipeline.trigger,
                "target_selector": pipeline.target_selector,
                "configuration": pipeline.configuration,
                "created_at": (
                    pipeline.created_at.isoformat()
                    if pipeline.created_at
                    else None
                ),
                "updated_at": (
                    pipeline.updated_at.isoformat()
                    if pipeline.updated_at
                    else None
                ),
                "steps": [
                    {
                        "id": step.id,
                        "position": step.position,
                        "name": step.name,
                        "type": step.type,
                        "configuration": step.configuration
                    }
                    for step in pipeline.steps
                ]
            }

        finally:

            session.close()

    def create_pipeline(
        self,
        name,
        description=None,
        status="active",
        trigger=None,
        target_selector=None,
        configuration=None
    ):

        session = get_session()

        try:

            pipeline = Pipeline(
                name=name,
                description=description,
                status=status,
                trigger=trigger or {},
                target_selector=target_selector or {},
                configuration=configuration or {}
            )

            session.add(pipeline)
            session.commit()
            session.refresh(pipeline)

            return self.get_pipeline(pipeline.id)

        except Exception:

            session.rollback()
            raise

        finally:

            session.close()

    def delete_pipeline(self, pipeline_id):

        session = get_session()

        try:

            pipeline = (
                session.query(Pipeline)
                .filter(Pipeline.id == pipeline_id)
                .first()
            )

            if pipeline is None:
                return False

            session.delete(pipeline)
            session.commit()

            return True

        except Exception:

            session.rollback()
            raise

        finally:

            session.close()

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
