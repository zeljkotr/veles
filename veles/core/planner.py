"""
veles/core/planner.py

Decides what Veles should DO with a given request: have an ordinary
chat, look up system status, remember a fact, or run a command.

Previously this was pure keyword matching (fast, free, but rigid - only
handled two fixed intents). Now a single call to the local model decides
the action AND, for run_command, the exact shell command to run. This
is more flexible ("pokreni nginx", "proveri da li radi docker", etc.)
but costs one model call per request instead of being instant/free -
worth it for the flexibility, and will matter less once running on
GPU hardware.
"""

from ..llm.ollama_client import call_ollama, extract_json


PLANNER_PROMPT_TEMPLATE = """

Ti si planer za AI asistenta po imenu Veles, koji radi na Linux serveru.

Tvoj zadatak je da analiziraš zahtev korisnika i odlučiš KOJU akciju treba izvršiti.

Dostupne akcije:
- "chat": običan razgovor ili pitanje - ne treba ništa izvršavati na sistemu
- "system_info": korisnik želi da vidi trenutno stanje sistema (CPU, RAM, disk)
- "remember_fact": korisnik eksplicitno traži da se nešto zapamti (npr. kaže "zapamti", "upamti", "seti se")
- "run_command": korisnik traži da se izvrši konkretna komanda na serveru (npr. "pokreni", "restartuj", "proveri da li radi X", "zaustavi")

Ako je akcija "run_command", u polju "command" napiši TAČNU shell komandu koju treba
izvršiti (npr. "systemctl status nginx", "systemctl restart nginx"). Ako akcija
NIJE "run_command", polje "command" ostavi prazno.

Vrati STROGO JSON, bez ikakvog dodatnog teksta:
{{"action": "...", "command": "..."}}

Zahtev korisnika: "{question}"

"""

VALID_ACTIONS = ("chat", "system_info", "remember_fact", "run_command")


def create_plan(question):
    prompt = PLANNER_PROMPT_TEMPLATE.format(question=question)
    raw = call_ollama(prompt, temperature=0.0, num_predict=120)
    parsed = extract_json(raw)

    if not parsed or "action" not in parsed:
        # If the planner call fails or returns something unparseable,
        # fall back to plain chat rather than silently guessing.
        return {"action": "chat", "command": ""}

    action = parsed.get("action", "chat")
    command = parsed.get("command", "") or ""

    if action not in VALID_ACTIONS:
        return {"action": "chat", "command": ""}

    return {"action": action, "command": command}
