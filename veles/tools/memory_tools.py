"""
veles/tools/memory_tools.py

Explicit-memory tool. Triggered when the user directly asks Veles to
remember something (e.g. "Veles, zapamti da server X koristi port 8080").
Uses the local model to pull a clean key/value pair out of the sentence,
then stores it via memory.remember().
"""

from ..memory.memory import remember
from ..llm.ollama_client import call_ollama, extract_json


def remember_fact(context):
    question = context["question"]

    prompt = f"""

Izdvoji ključnu činjenicu iz sledeće rečenice i vrati je STROGO u JSON formatu,
bez ikakvog dodatnog teksta, komentara ili objašnjenja - samo JSON.

Format: {{"key": "kratak naziv činjenice", "value": "sama vrednost/činjenica"}}

Rečenica: "{question}"

"""

    raw = call_ollama(prompt, temperature=0.0, num_predict=100)
    parsed = extract_json(raw)

    if parsed and parsed.get("key") and parsed.get("value"):
        key = parsed["key"]
        value = parsed["value"]
    else:
        # Fallback: store the whole sentence rather than silently losing it
        # if the model's JSON extraction didn't work out.
        key = "fact"
        value = question

    remember(key, value)

    return {"key": key, "value": value}
