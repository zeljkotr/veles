"""
VELES DATABASE CONNECTION
PostgreSQL + SQLAlchemy
"""


from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


# PostgreSQL connection

DATABASE_URL = (
    "postgresql+psycopg2://"
    "veles_app:Mia.0821@localhost:5432/veles"
)



# Engine

engine = create_engine(
    DATABASE_URL,
    echo=False
)



# Session

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)



def get_session():

    return SessionLocal()



def test_connection():

    try:

        with engine.connect() as connection:

            result = connection.execute(
                text("SELECT 1")
            )

            return result.fetchone()


    except Exception as e:

        print(
            "DATABASE ERROR:",
            e
        )

        return None