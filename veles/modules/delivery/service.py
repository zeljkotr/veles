"""
VELES Delivery Service

Prikuplja i upravlja stanjem
delivery sistema VELES.
"""

from veles.database.connection import get_session
from veles.database.models import Pipeline, PipelineStep
from veles.modules.infrastructure.resource_registry import ResourceRegistry


class DeliveryService:

    def __init__(self):

        self.resource_registry = ResourceRegistry()

        self.loaded = False

    def get_targets(self):

        return self.resource_registry.get_resources()

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

    def update_pipeline(
        self,
        pipeline_id,
        name,
        description=None,
        status=None,
        trigger=None,
        target_selector=None,
        configuration=None
    ):

        session = get_session()

        try:

            pipeline = (
                session.query(Pipeline)
                .filter(Pipeline.id == pipeline_id)
                .first()
            )

            if pipeline is None:
                return False

            pipeline.name = name
            pipeline.description = description

            if status is not None:
                pipeline.status = status

            if trigger is not None:
                pipeline.trigger = trigger

            if target_selector is not None:
                pipeline.target_selector = target_selector

            if configuration is not None:
                pipeline.configuration = configuration

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

    def add_pipeline_step(
        self,
        pipeline_id,
        position,
        name,
        type,
        configuration=None
    ):

        session = get_session()

        try:

            pipeline = (
                session.query(Pipeline)
                .filter(Pipeline.id == pipeline_id)
                .first()
            )

            if pipeline is None:
                return None

            step = PipelineStep(
                pipeline_id=pipeline_id,
                position=position,
                name=name,
                type=type,
                configuration=configuration or {}
            )

            session.add(step)
            session.commit()
            session.refresh(step)

            return {
                "id": step.id,
                "pipeline_id": step.pipeline_id,
                "position": step.position,
                "name": step.name,
                "type": step.type,
                "configuration": step.configuration
            }

        except Exception:

            session.rollback()
            raise

        finally:

            session.close()

    def get_pipeline_steps(self, pipeline_id):

        session = get_session()

        try:

            pipeline = (
                session.query(Pipeline)
                .filter(Pipeline.id == pipeline_id)
                .first()
            )

            if pipeline is None:
                return None

            steps = (
                session.query(PipelineStep)
                .filter(PipelineStep.pipeline_id == pipeline_id)
                .order_by(PipelineStep.position, PipelineStep.id)
                .all()
            )

            return [
                {
                    "id": step.id,
                    "pipeline_id": step.pipeline_id,
                    "position": step.position,
                    "name": step.name,
                    "type": step.type,
                    "configuration": step.configuration
                }
                for step in steps
            ]

        finally:

            session.close()

    def get_pipeline_step(self, step_id):

        session = get_session()

        try:

            step = (
                session.query(PipelineStep)
                .filter(PipelineStep.id == step_id)
                .first()
            )

            if step is None:
                return None

            return {
                "id": step.id,
                "pipeline_id": step.pipeline_id,
                "position": step.position,
                "name": step.name,
                "type": step.type,
                "configuration": step.configuration
            }

        finally:

            session.close()

    def update_pipeline_step(
        self,
        step_id,
        position=None,
        name=None,
        type=None,
        configuration=None
    ):

        session = get_session()

        try:

            step = (
                session.query(PipelineStep)
                .filter(PipelineStep.id == step_id)
                .first()
            )

            if step is None:
                return None

            if position is not None:
                step.position = position

            if name is not None:
                step.name = name

            if type is not None:
                step.type = type

            if configuration is not None:
                step.configuration = configuration

            session.commit()
            session.refresh(step)

            return {
                "id": step.id,
                "pipeline_id": step.pipeline_id,
                "position": step.position,
                "name": step.name,
                "type": step.type,
                "configuration": step.configuration
            }

        except Exception:

            session.rollback()
            raise

        finally:

            session.close()

    def delete_pipeline_step(self, step_id):

        session = get_session()

        try:

            step = (
                session.query(PipelineStep)
                .filter(PipelineStep.id == step_id)
                .first()
            )

            if step is None:
                return False

            session.delete(step)
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