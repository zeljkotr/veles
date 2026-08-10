"""
VELES Monitoring Service

Connects monitoring engine with infrastructure resources.
"""

from datetime import datetime

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



    def check_resource(
        self,
        resource: dict
    ):
        """
        Execute checks for one resource.
        """

        resource_id = resource.get(
            "id"
        )


        checks = resource.get(
            "checks",
            [
                "ping"
            ]
        )


        results = []


        for check in checks:

            result = run_check(
                check,
                resource
            )


            results.append(
                HealthCheckResult(
                    resource_id=resource_id,
                    check_type=check,
                    status=result.get(
                        "status"
                    ),
                    message=result.get(
                        "message"
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



        self.health[resource_id] = health



        return health



    def check_resources(
        self,
        resources: list
    ):
        """
        Check multiple resources.
        """

        results = []


        for resource in resources:

            results.append(
                self.check_resource(
                    resource
                )
            )


        return results



    def get_health(
        self,
        resource_id: str
    ):

        return self.health.get(
            resource_id
        )



    def get_all_health(self):

        return self.health



    def get_status(self):
        """
        VELES module status interface.
        Used by WEB dashboard.
        """

        return {

            "name": "Monitoring",

            "status": "active",

            "resources": list(
                self.health.values()
            ),

            "count": len(
                self.health
            )

        }



    def _calculate_status(
        self,
        results
    ):
        """
        Calculate global resource state.
        """

        if not results:

            return "unknown"



        statuses = [

            item.status

            for item in results

        ]



        if "offline" in statuses:

            return "critical"



        if "unknown" in statuses:

            return "warning"



        return "healthy"





# Global VELES monitoring instance

monitoring = MonitoringService()