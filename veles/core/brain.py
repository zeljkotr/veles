from .planner import create_plan
from .executor import Executor
from .reporter import create_report

from ..personality.personality import load_personality

from ..language_filter import clean_response, validate_serbian

from ..memory.memory import get_memory_text

from ..knowledge.search import get_knowledge_context

from ..llm.ollama_client import call_ollama, extract_json


executor = Executor()

MAX_LANGUAGE_RETRIES = 2


SYSTEM_RULES = """

STROGA PRAVILA ZA VELES:

JEZIK:

- Koristi srpski jezik.
- Koristi latinicu.
- Koristi ekavski standard.


STIL:

- Odgovaraj kao iskusan sistem inzenjer.
- Budi precizan i praktican.
- Ne pisi nepotrebne uvode.


LOKALNO ZNANJE:

- Ako postoji LOKALNO ZNANJE u promptu, koristi ga kao glavni izvor.
- Ne izmisljaj informacije koje nisu u lokalnom znanju.
- Ne menjaj komande iz dokumentacije.
- Na kraju odgovora navedi izvor dokumenta.


TEHNICKI ODGOVORI:

- Komande pisi u code blokovima.
- Objasnjavaj korak po korak.
- Ako nisi siguran reci da nisi siguran.

"""



def _detect_memorable_fact(question, answer):

    prompt = f"""

Analiziraj sledecu razmenu.

Ako postoji trajna cinjenica vredna pamcenja,
vrati samo JSON:

{{"key":"...","value":"..."}}

Ako ne postoji vrati:

{{}}

Bez dodatnog teksta.


Korisnik:

{question}


Veles:

{answer}

"""


    raw = call_ollama(
        prompt,
        temperature=0.0,
        num_predict=80
    )


    parsed = extract_json(raw)


    if parsed and parsed.get("key") and parsed.get("value"):
        return parsed


    return None



def ask_veles(question):


    plan = create_plan(question)

    print("PLAN:", plan)


    if plan["action"] != "chat":


        tool_result = executor.execute(
            plan["action"],
            {
                "question": question,
                "plan": plan
            }
        )


        return {
            "answer": create_report(tool_result),
            "suggested_memory": None
        }



    personality = load_personality()


    memory = get_memory_text()


    knowledge = get_knowledge_context(question)


    print("\n========== LOKALNO ZNANJE ==========")
    print(knowledge)
    print("=====================================\n")



    prompt = f"""

{personality}


MEMORIJA:

{memory}


LOKALNO ZNANJE:

{knowledge}


{SYSTEM_RULES}


Korisnik:

{question}


Veles:

"""



    print("Veles razmislja...")


    answer = ""


    for attempt in range(MAX_LANGUAGE_RETRIES + 1):


        raw_answer = call_ollama(
            prompt,
            temperature=0.2,
            num_predict=250
        )


        answer = clean_response(raw_answer)


        if validate_serbian(answer):
            break


        print(
            "[veles] Jezik nije prosao proveru "
            f"({attempt + 1}/{MAX_LANGUAGE_RETRIES})"
        )



    suggested_memory = _detect_memorable_fact(
        question,
        answer
    )


    return {
        "answer": answer,
        "suggested_memory": suggested_memory
    }