from .planner import create_plan
from .executor import Executor
from .reporter import create_report

from ..personality.personality import load_personality

from ..language_filter import clean_response, validate_serbian

from ..memory.memory import get_memory_text

from ..llm.ollama_client import call_ollama, extract_json


executor = Executor()

MAX_LANGUAGE_RETRIES = 2


SYSTEM_RULES = """

STROGA PRAVILA:

JEZIK:

- Piši isključivo srpskim jezikom.
- Koristi latinicu.
- Nikada ne koristi ćirilicu.
- Koristi ekavski standard.


STIL:

- Odgovaraj kao iskusan sistem inženjer.
- Budi precizan.
- Budi praktičan.
- Koristi jasne rečenice.


TEHNIČKI ODGOVORI:

- Komande piši u code blokovima.
- Objašnjavaj korak po korak.
- Ako nisi siguran reci da nisi siguran.

"""


def _detect_memorable_fact(question, answer):
    """
    Lightweight second pass after an ordinary chat exchange: asks the
    model whether anything in it is worth remembering long-term (a
    stated preference, a fact about Zeljko's environment, a decision) -
    NOT a routine technical question with no lasting value. Returns
    None for the vast majority of exchanges, which is expected.
    """
    prompt = f"""

Analiziraj sledeću razmenu i oceni da li sadrži TRAJNU činjenicu vrednu
pamćenja (npr. lični podatak, preferenca, odluka, konfiguracija sistema) -
NE običnu tehničko pitanje ili odgovor bez trajne vrednosti.

Ako POSTOJI takva činjenica, vrati STROGO JSON: {{"key": "...", "value": "..."}}
Ako NE POSTOJI, vrati STROGO: {{}}
Bez ikakvog dodatnog teksta.

Korisnik: {question}
Veles: {answer}

"""
    raw = call_ollama(prompt, temperature=0.0, num_predict=80)
    parsed = extract_json(raw)

    if parsed and parsed.get("key") and parsed.get("value"):
        return parsed
    return None


def ask_veles(question):
    """
    Returns a dict: {"answer": str, "suggested_memory": dict|None}.
    suggested_memory, when present, is a {"key", "value"} pair the
    caller (main.py) should offer to save - Veles never saves an
    auto-detected fact without the user confirming it first.
    """

    plan = create_plan(question)

    print("PLAN:", plan)

    if plan["action"] != "chat":

        tool_result = executor.execute(
            plan["action"],
            question
        )

        return {"answer": create_report(tool_result), "suggested_memory": None}

    personality = load_personality()

    memory = get_memory_text()

    prompt = f"""

{personality}


{memory}


{SYSTEM_RULES}


Korisnik:

{question}


Veles:

"""

    print("Veles razmišlja...")

    answer = ""
    for attempt in range(MAX_LANGUAGE_RETRIES + 1):
        raw_answer = call_ollama(prompt, temperature=0.2, num_predict=200)
        answer = clean_response(raw_answer)

        if validate_serbian(answer):
            break

        print(f"[veles] Odgovor je sadržao ćirilicu, pokušavam ponovo "
              f"({attempt + 1}/{MAX_LANGUAGE_RETRIES})...")
    else:
        print("[veles] Nisam uspeo da dobijem čist latinični odgovor "
              "posle svih pokušaja - vraćam poslednji dobijeni.")

    suggested_memory = _detect_memorable_fact(question, answer)

    return {"answer": answer, "suggested_memory": suggested_memory}