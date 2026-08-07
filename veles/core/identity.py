from uuid import uuid4
from datetime import datetime, timezone


class IdentityService:

    @staticmethod
    def create(resource):

        identity = resource.get("identity") or {}

        if "internal_id" not in identity:
            identity["internal_id"] = str(uuid4())

        identity.setdefault(
            "version",
            1
        )

        identity.setdefault(
            "created_at",
            datetime.now(timezone.utc).isoformat()
        )

        identity.setdefault(
            "hostname",
            resource.get("name")
        )

        identity.setdefault(
            "tailscale_ip",
            resource.get("host")
        )

        identity.setdefault("fqdn", None)
        identity.setdefault("ipv4", None)
        identity.setdefault("ipv6", None)
        identity.setdefault("agent_id", None)
        identity.setdefault("certificate", None)
        identity.setdefault("hardware_id", None)

        return identity


    @staticmethod
    def update(resource, **kwargs):

        identity = resource.get("identity") or {}

        protected = [
            "internal_id",
            "created_at"
        ]

        for key, value in kwargs.items():

            if key not in protected:
                identity[key] = value

        return identity


    @staticmethod
    def get(resource):

        return resource.get("identity") or {}


    @staticmethod
    def validate(identity):

        required = [
            "internal_id",
            "version",
            "created_at"
        ]

        return all(
            field in identity
            for field in required
        )