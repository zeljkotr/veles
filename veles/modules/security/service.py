"""
VELES Security Service

Main local security inspection service.
"""

from veles.modules.security.models import (
    SecurityCheckResult,
    SecurityReport
)

from veles.modules.security.checks import (
    check_users,
    check_privileged_users,
    check_listening_ports,
    check_services,
    check_ssh,
    check_firewall,
    check_system
)


class SecurityService:
    """
    Main VELES security service.

    Read-only in v1.
    """

    def __init__(self):

        self.report = None


    def run_check(self, check_type):
        """
        Execute one security check.
        """

        checks = {
            "users": check_users,
            "privileged_users": check_privileged_users,
            "listening_ports": check_listening_ports,
            "services": check_services,
            "ssh": check_ssh,
            "firewall": check_firewall,
            "system": check_system
        }

        check = checks.get(
            check_type
        )

        if check is None:

            return SecurityCheckResult(
                check_type=check_type,
                status="unknown",
                message=(
                    f"Unknown security check: {check_type}"
                )
            )

        try:

            result = check()

            return SecurityCheckResult(
                check_type=check_type,
                status=result.get(
                    "status",
                    "ok"
                ),
                message=result.get(
                    "message",
                    ""
                ),
                data=result.get(
                    "data"
                )
            )

        except Exception as e:

            return SecurityCheckResult(
                check_type=check_type,
                status="error",
                message=str(e)
            )


    def scan(self):
        """
        Run complete local security inspection.
        """

        check_types = [
            "system",
            "users",
            "privileged_users",
            "listening_ports",
            "services",
            "ssh",
            "firewall"
        ]

        results = []

        for check_type in check_types:

            results.append(
                self.run_check(
                    check_type
                )
            )

        status = self._calculate_status(
            results
        )

        report = SecurityReport(
            status=status,
            checks=results,
            summary=self._build_summary(
                results
            )
        )

        self.report = report

        return report


    def get_report(self):

        return self.report


    def get_status(self):
        """
        VELES module status interface.
        """

        report = self.report

        return {
            "name": "Security",
            "status": (
                report.status
                if report
                else "not_scanned"
            ),
            "checks": (
                report.checks
                if report
                else []
            ),
            "summary": (
                report.summary
                if report
                else {}
            )
        }


    def _calculate_status(
        self,
        results
    ):
        """
        Calculate overall security inspection state.
        """

        if not results:

            return "unknown"

        error_count = sum(
            1
            for result in results
            if result.status == "error"
        )

        if error_count:

            return "warning"

        return "healthy"


    def _build_summary(
        self,
        results
    ):
        """
        Build compact security summary.
        """

        summary = {
            "total_checks": len(results),
            "healthy": 0,
            "warning": 0,
            "error": 0,
            "unknown": 0
        }

        for result in results:

            if result.status in summary:

                summary[
                    result.status
                ] += 1

            else:

                summary["unknown"] += 1

        return summary


security = SecurityService()