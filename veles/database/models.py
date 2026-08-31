"""
VELES DATABASE MODELS
SQLAlchemy ORM
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class Resource(Base):

    __tablename__ = "resources"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    type = Column(
        String(50),
        nullable=False
    )

    name = Column(
        String(100),
        nullable=False
    )

    host = Column(
        String(100)
    )

    port = Column(
        String(20)
    )

    username = Column(
        String(100)
    )

    group = Column(
        String(100)
    )

    status = Column(
        String(50),
        default="registered"
    )

    verification = Column(
        JSON,
        default={}
    )

    trust = Column(
        String(50),
        default="unknown"
    )

    identity = Column(
        JSON,
        default={}
    )

    policy = Column(
        JSON,
        default={}
    )

    actions = Column(
        JSON,
        default={}
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class AuditLog(Base):

    __tablename__ = "audit_logs"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    time = Column(
        DateTime,
        default=datetime.utcnow
    )

    actor = Column(
        String(100)
    )

    resource_id = Column(
        Integer
    )

    action = Column(
        String(100)
    )

    result = Column(
        String(100)
    )


class Pipeline(Base):

    __tablename__ = "pipelines"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    name = Column(
        String(150),
        nullable=False,
        unique=True
    )

    description = Column(
        String(500)
    )

    status = Column(
        String(50),
        nullable=False,
        default="active"
    )

    trigger = Column(
        JSON,
        default={}
    )

    target_selector = Column(
        JSON,
        default={}
    )

    configuration = Column(
        JSON,
        default={}
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    steps = relationship(
        "PipelineStep",
        back_populates="pipeline",
        cascade="all, delete-orphan",
        order_by="PipelineStep.position"
    )


class PipelineStep(Base):

    __tablename__ = "pipeline_steps"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    pipeline_id = Column(
        Integer,
        ForeignKey("pipelines.id"),
        nullable=False
    )

    position = Column(
        Integer,
        nullable=False,
        default=0
    )

    name = Column(
        String(150),
        nullable=False
    )

    type = Column(
        String(50),
        nullable=False
    )

    configuration = Column(
        JSON,
        default={}
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    pipeline = relationship(
        "Pipeline",
        back_populates="steps"
    )
