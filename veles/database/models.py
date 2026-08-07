"""
VELES DATABASE MODELS
SQLAlchemy ORM
"""


from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import declarative_base
from datetime import datetime



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

