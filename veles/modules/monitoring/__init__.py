"""
VELES Monitoring Module
"""

from veles.modules.monitoring.service import (
    monitoring,
    MonitoringService
)

from veles.modules.monitoring.scheduler import (
    MonitoringScheduler
)


__all__ = [
    "monitoring",
    "MonitoringService",
    "MonitoringScheduler"
]