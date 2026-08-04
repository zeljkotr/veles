from pathlib import Path


# Koreni direktorijum znanja
KNOWLEDGE_DIR = Path(__file__).resolve().parent


SUPPORTED_FILES = [
    ".md",
    ".txt"
]


def find_documents():
    """
    Pronalazi sve dokumente u knowledge folderu.
    """

    documents = []

    for file in KNOWLEDGE_DIR.rglob("*"):

        if file.is_file() and file.suffix.lower() in SUPPORTED_FILES:

            documents.append(file)

    return documents



def load_document(file_path):
    """
    Učitava jedan dokument.
    """

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            return {
                "name": file_path.name,
                "path": str(file_path),
                "content": file.read()
            }


    except Exception as e:

        return {
            "name": file_path.name,
            "path": str(file_path),
            "error": str(e)
        }



def load_all_knowledge():
    """
    Učitava kompletnu bazu znanja.
    """

    knowledge = []

    documents = find_documents()


    for document in documents:

        loaded = load_document(document)

        knowledge.append(loaded)


    return knowledge



def knowledge_count():
    """
    Broj dostupnih dokumenata.
    """

    return len(find_documents())
