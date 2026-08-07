"""
VELES DATABASE INITIALIZATION
Creates PostgreSQL tables
"""


from veles.database.connection import engine
from veles.database.models import Base



def init_database():

    print("Creating database tables...")

    Base.metadata.create_all(
        bind=engine
    )

    print("Database ready.")



if __name__ == "__main__":

    init_database()