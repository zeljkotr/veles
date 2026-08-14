"""
VELES Monitoring Service

Connects monitoring engine with infrastructure resources.
"""

from datetime import datetime
from threading import RLock

from veles.modules.monitoring.models import (
    HealthCheckResult,
    ResourceHealth
)

from veles.modules.monitoring.checks import (
    run_check
)


class MonitoringService:
    """
    Main monitoring service.
    """

    def __init__(self):

        self.health = {}

        self._lock = RLock()


    def check_resource(
        self,
        resource: dict
    ):
        """
        Execute checks for one resource.
        """

        if not isinstance(resource, dict):

            return None


        resource_id = resource.get(
            "id"
        )


        if resource_id is None:

            return None


        resource_id = str(
            resource_id
        )


        checks = self._get_checks(
            resource
        )


        results = []


        for check in checks:

            try:

                result = run_check(
                    check,
                    resource
                )

            except Exception as exc:

                result = {
                    "status": "unknown",
                    "message": str(exc),
                    "response_time_ms": None
                }


            results.append(
                HealthCheckResult(

                    resource_id=resource_id,

                    check_type=str(
                        check
                    ),

                    status=result.get(
                        "status",
                        "unknown"
                    ),

                    message=result.get(
                        "message",
                        ""
                    ),

                    response_time_ms=result.get(
                        "response_time_ms"
                    )
                )
            )


        status = self._calculate_status(
            results
        )


        health = ResourceHealth(

            resource_id=resource_id,

            status=status,

            checks=results,

            last_check=datetime.now().isoformat()
        )


        with self._lock:

            self.health[
                resource_id
            ] = health


        return health


    def check_resources(
        self,
        resources: list
    ):
        """
        Check multiple resources.
        """

        results = []


        if not resources:

            return results


        for resource in resources:

            try:

                result = self.check_resource(
                    resource
                )

                if result is not None:

                    results.append(
                        result
                    )

            except Exception as exc:

                print(
                    "[MONITORING RESOURCE ERROR]",
                    exc
                )


        return results


    def get_health(
        self,
        resource_id
    ):

        if resource_id is None:

            return None


        key = str(
            resource_id
        )


        with self._lock:

            return self.health.get(
                key
            )


    def get_all_health(self):

        with self._lock:

            return dict(
                self.health
            )


    def get_status(self):
        """
        VELES module status interface.
        Used by WEB dashboard.
        """

        with self._lock:

            resources = list(
                self.health.values()
            )


        return {

            "name": "Monitoring",

            "status": "active",

            "resources": resources,

            "count": len(
                resources
            )

        }


    def _get_checks(
        self,
        resource: dict
    ):
        """
        Resolve checks from the resource.

        Existing resources do not contain monitoring
        configuration, so ping remains the safe default.

        Future monitoring configuration may be supplied
        through:

            resource["checks"]

        or:

            resource["monitoring"]["checks"]
        """

        checks = resource.get(
            "checks"
        )


        if checks is None:

            monitoring_config = resource.get(
                "monitoring"
            )

            if isinstance(
                monitoring_config,
                dict
            ):

                checks = monitoring_config.get(
                    "checks"
                )


        if isinstance(
            checks,
            str
        ):

            checks = [
                checks
            ]


        if not isinstance(
            checks,
            (list, tuple)
        ):

            checks = [
                "ping"
            ]


        normalized = []


        for check in checks:

            value = str(
                check
            ).strip().lower()


            if value and value not in normalized:

                normalized.append(
                    value
                )


        if not normalized:

            normalized = [
                "ping"
            ]


        return normalized


    def _calculate_status(
        self,
        results
    ):
        """
        Calculate global resource state.

        Priority:

            CRITICAL
            WARNING
            UNKNOWN
            HEALTHY
        """

        if not results:

            return "unknown"


        statuses = [

            str(
                item.status
            ).strip().lower()

            for item in results

        ]


        # Any offline check makes the whole
        # resource CRITICAL.
        if "offline" in statuses:

            return "critical"


        # Explicit warning remains WARNING.
        if "warning" in statuses:

            return "warning"


        # Unknown remains UNKNOWN.
        # It must not be silently converted
        # into WARNING.
        if "unknown" in statuses:

            return "unknown"


        # All checks passed.
        return "healthy"


# Global VELES monitoring instance

monitoring = MonitoringService()