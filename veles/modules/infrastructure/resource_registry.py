"""
Veles Infrastructure Resource Registry

Centralni registar svih infrastrukturnih resursa.

Storage:
PostgreSQL (primary)
"""


from veles.database.connection import get_session
from veles.database.models import Resource
from veles.core.identity import IdentityService



class ResourceRegistry:


    def __init__(self):

        pass



    def add_resource(self, resource):

        """
        Dodavanje resursa u PostgreSQL bazu.
        Sprečava duplikate:
        type + name + host
        """

        session = get_session()

        try:

            existing = session.query(
                Resource
            ).filter(

                Resource.type == resource.get(
                    "type",
                    "server"
                ),

                Resource.name == resource.get(
                    "name",
                    "Unknown"
                ),

                Resource.host == resource.get(
                    "host"
                )

            ).first()


            if existing:

                return self._to_dict(
                    existing
                )


            resource["identity"] = IdentityService.create(
                resource
            )


            db_resource = Resource(

                type=resource.get(
                    "type",
                    "server"
                ),

                name=resource.get(
                    "name",
                    "Unknown"
                ),

                host=resource.get(
                    "host"
                ),

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



    def get_resources(self, group=None):

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

                self._to_dict(item)

                for item in resources

            ]


        finally:

            session.close()



    def get_resource(self, resource_id):

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



    def update_resource(self, resource_id, data):

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



    def delete_resource(self, resource_id):

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



    def update_verification(self, resource_id, verification):

        self.update_resource(
        resource_id,
        {
            "verification": verification
        }
    )



    def _to_dict(self, item):

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

            "trust":
                item.trust or "unknown",

            "identity":
                item.identity or {},

            "policy":
                item.policy or {},

            "actions":
                item.actions or {}

        }