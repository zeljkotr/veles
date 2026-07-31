from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


PERSONALITY_FILE = BASE_DIR / "config" / "personality.md"



def load_personality():

    with open(
        PERSONALITY_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return file.read()