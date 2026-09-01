"""
Veles Infrastructure Resource Registry

Centralni registar svih infrastrukturnih resursa.

Storage:
PostgreSQL (primary)

Discovery resources:
--------------------

Resources created from Discovery use the
"Discovered-<host>" naming convention.

For discovered resources, the host is the
unique identity. A discovered host must not
be registered again with another resource type.

Manually created resources keep the existing
type + name + host duplicate protection.
"""

from veles.database.connection import get_session
from veles.database.models import Resource
from veles.core.identity import IdentityService


class ResourceRegistry:

    def __init__(self):

        pass


    def add_resource(
        self,
        resource
    ):

        """
        Dodavanje resursa u PostgreSQL bazu.

        Discovery resources:
            - unique by host when name starts
              with "Discovered-"

        Other resources:
            - duplicate protection remains:
              type + name + host

        Vraća postojeći resource ako već postoji.
        """

        if not isinstance(
            resource,
            dict
        ):

            return None


        session = get_session()

        try:

            resource_type = resource.get(
                "type",
                "server"
            )

            resource_name = resource.get(
                "name",
                "Unknown"
            )

            resource_host = resource.get(
                "host"
            )


            # =================================================
            # DISCOVERY DUPLICATE PROTECTION
            # =================================================

            is_discovered = (

                isinstance(
                    resource_name,
                    str
                )

                and resource_name.startswith(
                    "Discovered-"
                )

                and resource_host

            )


            if is_discovered:

                existing = session.query(
                    Resource
                ).filter(
                    Resource.host == resource_host,
                    Resource.name.like(
                        "Discovered-%"
                    )
                ).first()


                if existing:

                    return self._to_dict(
                        existing
                    )


            # =================================================
            # NORMAL RESOURCE DUPLICATE PROTECTION
            # =================================================

            existing = session.query(
                Resource
            ).filter(
                Resource.type == resource_type,
                Resource.name == resource_name,
                Resource.host == resource_host
            ).first()


            if existing:

                return self._to_dict(
                    existing
                )


            # =================================================
            # CREATE IDENTITY
            # =================================================

            resource["identity"] = IdentityService.create(
                resource
            )


            # =================================================
            # CREATE DATABASE RESOURCE
            # =================================================

            db_resource = Resource(

                type=resource_type,

                name=resource_name,

                host=resource_host,

                port=resource.get(
                    "port"
                ),

                username=resource.get(
                    "username"
                ),

                group=resource.get(
                    "group"
                ),

                status=resource.get(
                    "status",
                    "registered"
                ),

                verification={
                    **(
                        resource.get("verification")
                        or {}
                    ),
                    "os": resource.get("os"),
                    "ports": resource.get(
                        "ports",
                        []
                    ),
                    "services": resource.get(
                        "services",
                        []
                    )
                },

                identity=resource.get(
                    "identity"
                )

            )


            session.add(
                db_resource
            )


            session.commit()


            session.refresh(
                db_resource
            )


            return self._to_dict(
                db_resource
            )


        finally:

            session.close()


    def get_resources(
        self,
        group=None
    ):

        session = get_session()

        try:

            query = session.query(
                Resource
            )


            if group:

                query = query.filter(
                    Resource.type == group.rstrip("s")
                )


            resources = query.all()


            return [

                self._to_dict(
                    item
                )

                for item in resources

            ]


        finally:

            session.close()


    def get_resource(
        self,
        resource_id
    ):

        session = get_session()

        try:

            resource = session.query(
                Resource
            ).filter(
                Resource.id == resource_id
            ).first()


            if resource:

                return self._to_dict(
                    resource
                )


            return None


        finally:

            session.close()


    def update_resource(
        self,
        resource_id,
        data
    ):

        session = get_session()

        try:

            resource = session.query(
                Resource
            ).filter(
                Resource.id == resource_id
            ).first()


            if not resource:

                return None


            for key, value in data.items():

                if hasattr(
                    resource,
                    key
                ):

                    setattr(
                        resource,
                        key,
                        value
                    )


            session.commit()


            session.refresh(
                resource
            )


            return self._to_dict(
                resource
            )


        finally:

            session.close()


    def delete_resource(
        self,
        resource_id
    ):

        session = get_session()

        try:

            resource = session.query(
                Resource
            ).filter(
                Resource.id == resource_id
            ).first()


            if not resource:

                return False


            session.delete(
                resource
            )


            session.commit()


            return True


        finally:

            session.close()


    def update_verification(
        self,
        resource_id,
        verification
    ):

        self.update_resource(

            resource_id,

            {
                "verification": verification
            }

        )


    def _to_dict(
        self,
        item
    ):

        """
        SQLAlchemy model -> dict
        """

        return {

            "id":
                item.id,

            "type":
                item.type,

            "name":
                item.name,

            "host":
                item.host,

            "port":
                item.port,

            "username":
                item.username,

            "group":
                item.group,

            "status":
                item.status,

            "verification":
                item.verification or {},

            "os":
                (item.verification or {}).get("os"),

            "ports":
                (item.verification or {}).get(
                    "ports",
                    []
                ),

            "services":
                (item.verification or {}).get(
                    "services",
                    []
                ),

            "trust":
                item.trust or "unknown",

            "identity":
                item.identity or {},

            "policy":
                item.policy or {},

            "actions":
                item.actions or {}

        }