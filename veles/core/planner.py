"""
veles/core/planner.py

Planner for Veles AI assistant.

Decision order:
1. Local rules
2. Ollama planner
"""

import re

from ..llm.ollama_client import call_ollama, extract_json


PLANNER_PROMPT_TEMPLATE = """

Ti si planer za AI asistenta Veles.

Odredi akciju korisnika.

Akcije:

- chat:
  Pitanje, objasnjenje, ucenje.
  Ne izvrsavaj komande.

- system_info:
  Korisnik trazi stanje sistema.

- remember_fact:
  Korisnik trazi pamcenje informacije.

- run_command:
  Korisnik direktno trazi izvrsavanje komande.


Primer:

Korisnik:
Kako restartujem linux servis

Odgovor:

{{
"action": "chat",
"command": ""
}}


Korisnik:
Restartuj nginx

Odgovor:

{{
"action": "run_command",
"command": "systemctl restart nginx"
}}


Vrati samo JSON:

{{
"action": "...",
"command": "..."
}}


Zahtev:

"{question}"

"""


VALID_ACTIONS = (
    "chat",
    "system_info",
    "remember_fact",
    "run_command"
)



def local_intent_check(question):

    q = question.lower().strip()


    explanation_patterns = [
        r"^kako ",
        r"^sta ",
        r"^šta ",
        r"^objasni",
        r"^zasto ",
        r"^zašto "
    ]


    for pattern in explanation_patterns:

        if re.search(pattern, q):

            return {
                "action": "chat",
                "command": ""
            }



    system_words = [
        "proveri sistem",
        "stanje sistema",
        "cpu",
        "ram",
        "memorija",
        "disk"
    ]


    for word in system_words:

        if word in q:

            return {
                "action": "system_info",
                "command": ""
            }



    commands = [
        "restartuj ",
        "restartaj ",
        "pokreni ",
        "startuj ",
        "zaustavi ",
        "ugasi "
    ]


    for cmd in commands:

        if cmd in q:

            service = q.split(cmd, 1)[1].strip()

            if service:

                return {
                    "action": "run_command",
                    "command": f"systemctl restart {service}"
                }



    return None




def create_plan(question):

    local_plan = local_intent_check(question)

    if local_plan:

        return local_plan



    prompt = PLANNER_PROMPT_TEMPLATE.format(
        question=question
    )


    raw = call_ollama(
        prompt,
        temperature=0.0,
        num_predict=120
    )


    parsed = extract_json(raw)


    if not parsed or "action" not in parsed:

        return {
            "action": "chat",
            "command": ""
        }



    action = parsed.get(
        "action",
        "chat"
    )


    command = parsed.get(
        "command",
        ""
    ) or ""



    if action not in VALID_ACTIONS:

        return {
            "action": "chat",
            "command": ""
        }



    return {
        "action": action,
        "command": command
    }