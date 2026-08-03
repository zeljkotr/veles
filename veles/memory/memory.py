import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).parent / "veles.db"


def get_connection():

    return sqlite3.connect(DB_PATH)


def init_memory():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memories (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        key TEXT NOT NULL,

        value TEXT NOT NULL

    )
    """)

    conn.commit()
    conn.close()



def remember(key, value):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO memories (key, value)
        VALUES (?, ?)
        """,
        (
            key,
            value
        )
    )

    conn.commit()
    conn.close()



def recall():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT key, value
        FROM memories
        ORDER BY id ASC
        """
    )

    result = cursor.fetchall()

    conn.close()

    return result


def recall_with_ids():
    """Same as recall() but includes each row's id - needed so the web
    interface can offer a delete button per memory entry."""

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, key, value
        FROM memories
        ORDER BY id ASC
        """
    )

    result = cursor.fetchall()

    conn.close()

    return result


def delete_memory(memory_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM memories WHERE id = ?",
        (memory_id,)
    )

    conn.commit()
    conn.close()



def get_memory_text():

    memories = recall()


    if not memories:

        return ""


    text = """

INFORMACIJE KOJE VELES PAMTI:

"""


    for key, value in memories:

        text += f"- {key}: {value}\n"


    return text



# automatska inicijalizacija baze

init_memory()
