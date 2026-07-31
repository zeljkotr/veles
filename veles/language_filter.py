import re


CYRILLIC_PATTERN = re.compile(
    r"[\u0400-\u04FF]"
)


def contains_cyrillic(text):

    return bool(
        CYRILLIC_PATTERN.search(text)
    )


def clean_response(text):

    text = text.strip()

    text = re.sub(
        r"[ ]{2,}",
        " ",
        text
    )

    return text


def validate_serbian(text):

    if contains_cyrillic(text):
        return False

    return True