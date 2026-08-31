"""
VELES Security Service

Main local security inspection service.

Security is read-only.

This service is responsible for:
- discovering the current local inspection target
- executing registered security checks
- attaching target context to every result
- building the final security report

Remote security will use the same result model later, but through
separate remote connectors.
"""

import getpass
import platform
import socket

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
    check_system,
    check_file_permissions
)


class SecurityService:
    """
    Main VELES security service.

    Current implementation:
        LOCAL / READ-ONLY

    No system configuration is changed.
    """

    def __init__(self):
        self.report = None


    def _get_local_target(self):
        """
        Discover the current local security inspection target.

        No hostname, username, IP address, interface or other
        machine-specific value is hardcoded.
        """

        try:
            hostname = socket.gethostname()
        except Exception:
            hostname = "unknown"

        try:
            fqdn = socket.getfqdn()
        except Exception:
            fqdn = hostname

        try:
            user = getpass.getuser()
        except Exception:
            user = "unknown"

        try:
            system = platform.system()
        except Exception:
            system = "unknown"

        try:
            release = platform.release()
        except Exception:
            release = "unknown"

        try:
            machine = platform.machine()
        except Exception:
            machine = "unknown"

        return {
            "scope": "local",

            "target": {
                "name": hostname,
                "hostname": hostname,
                "fqdn": fqdn,
                "host": hostname,
                "platform": system.lower(),
                "os": system,
                "release": release,
                "architecture": machine,
                "user": user
            },

            "connector": {
                "type": "local",
                "mode": "direct"
            }
        }


    def run_check(
        self,
        check_type,
        target_metadata=None
    ):
        """
        Execute one security check.

        Target metadata is attached to the result without changing
        the existing check implementation.
        """

        checks = {
            "users": check_users,
            "privileged_users": check_privileged_users,
            "listening_ports": check_listening_ports,
            "services": check_services,
            "ssh": check_ssh,
            "firewall": check_firewall,
            "system": check_system,
            "file_permissions": check_file_permissions
        }

        check = checks.get(check_type)

        if check is None:

            return SecurityCheckResult(
                check_type=check_type,
                status="unknown",
                message=f"Unknown security check: {check_type}",
                metadata=dict(target_metadata or {})
            )

        try:

            result = check()

            metadata = dict(
                target_metadata or {}
            )

            result_metadata = result.get(
                "metadata",
                {}
            )

            if isinstance(
                result_metadata,
                dict
            ):
                metadata.update(
                    result_metadata
                )

            return SecurityCheckResult(
                check_type=check_type,
                status=result.get(
                    "status",
                    "unknown"
                ),
                message=result.get(
                    "message",
                    ""
                ),
                data=result.get(
                    "data"
                ),
                metadata=metadata
            )

        except Exception as e:

            return SecurityCheckResult(
                check_type=check_type,
                status="error",
                message=str(e),
                metadata=dict(
                    target_metadata or {}
                )
            )


    def scan(self):
        """
        Run complete local security inspection.
        """

        target_metadata = (
            self._get_local_target()
        )

        check_types = [
            "system",
            "users",
            "privileged_users",
            "listening_ports",
            "services",
            "ssh",
            "firewall",
            "file_permissions"
        ]

        results = []

        for check_type in check_types:

            results.append(
                self.run_check(
                    check_type,
                    target_metadata
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
            ),
            metadata=target_metadata
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
            ),

            "metadata": (
                report.metadata
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

        UNKNOWN does not automatically make the whole system
        unhealthy. This is important for checks such as firewall
        inspection when the VELES process lacks root privileges.
        """

        if not results:
            return "unknown"

        has_error = any(
            result.status == "error"
            for result in results
        )

        if has_error:
            return "error"

        has_warning = any(
            result.status == "warning"
            for result in results
        )

        if has_warning:
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

                summary[
                    "unknown"
                ] += 1

        return summary


security = SecurityService()
