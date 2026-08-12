"""
Veles Infrastructure Models

Osnovni objekti infrastrukture:

- Server
- Device
- Agent
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Server:

    name: str

    hostname: str

    ip: str

    os: str

    status: str = "unknown"

    last_seen: Optional[str] = None

    cpu: str = "unknown"

    memory: dict = None

    disk: dict = None

    uptime: str = "unknown"


    def touch(self):

        self.last_seen = datetime.now().isoformat()

        self.status = "online"


@dataclass
class Device:

    name: str

    device_type: str

    ip: str

    status: str = "unknown"


@dataclass
class Agent:

    name: str

    hostname: str

    version: str

    status: str = "offline"