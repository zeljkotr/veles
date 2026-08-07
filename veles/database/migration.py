"""
VELES DATABASE MIGRATION
JSON Resource Registry -> PostgreSQL
"""


import json
from pathlib import Path

from veles.database.connection import get_session
from veles.database.models import Resource



BASE_DIR = Path(__file__).resolve().parent

JSON_FILE = BASE_DIR / "resources.json"



def load_json():

    with open(JSON_FILE, "r", encoding="utf-8") as file:

        return json.load(file)



def resource_exists(
    session,
    resource_type,
    name,
    host
):

    return session.query(Resource).filter_by(
        type=resource_type,
        name=name,
        host=host
    ).first()



def migrate():


    print()
    print("=== VELES RESOURCE MIGRATION ===")
    print()


    data = load_json()


    session = get_session()


    added = 0
    skipped = 0
    errors = 0
    total = 0


    try:

        for category, resources in data.items():


            for item in resources:

                total += 1


                try:


                    resource_type = item.get(
                        "type",
                        category.rstrip("s")
                    )


                    name = item.get(
                        "name"
                    )


                    host = item.get(
                        "host"
                    )


                    if not name:

                        print(
                            "SKIP: Resource without name"
                        )

                        skipped += 1
                        continue



                    existing = resource_exists(
                        session,
                        resource_type,
                        name,
                        host
                    )


                    if existing:


                        print(
                            "DUPLICATE:",
                            name
                        )

                        skipped += 1
                        continue



                    resource = Resource(

                        type=resource_type,

                        name=name,

                        host=host,

                        port=item.get(
                            "port"
                        ),

                        username=item.get(
                            "username"
                        ),

                        group=item.get(
                            "group"
                        ),

                        status=item.get(
                            "status",
                            "registered"
                        )

                    )


                    session.add(resource)


                    print(
                        "ADD:",
                        name
                    )


                    added += 1



                except Exception as e:

                    errors += 1

                    print(
                        "ERROR:",
                        item,
                        e
                    )


        session.commit()



    finally:

        session.close()



    print()
    print("=== RESULT ===")
    print(
        "Total:",
        total
    )

    print(
        "Added:",
        added
    )

    print(
        "Skipped:",
        skipped
    )

    print(
        "Errors:",
        errors
    )

    print()



if __name__ == "__main__":

    migrate()