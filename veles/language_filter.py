"""
VELES Language Filter

Cleans and validates AI responses before they are returned
to the VELES user interface.
"""

import re


def clean_response(text: str) -> str:
    """
    Clean an AI response for presentation in VELES.
    """

    if not text:
        return ""

    text = str(text).strip()

    # Remove Markdown code fences.
    text = re.sub(r"```[a-zA-Z0-9_+-]*\s*", "", text)
    text = text.replace("```", "")

    # Remove Markdown headings.
    text = re.sub(r"^\s{0,3}#{1,6}\s+", "", text, flags=re.MULTILINE)

    # Remove Markdown emphasis markers.
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("*", "")
    text = text.replace("_", "")

    # Remove inline code markers.
    text = text.replace("`", "")

    # Normalize excessive blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def validate_serbian(text: str) -> bool:
    """
    Validate that the response contains usable text.
    """

    if not text or not text.strip():
        return False

    normalized = re.sub(r"\s+", "", text)

    if not normalized:
        return False

    return True
