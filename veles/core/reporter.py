from ..llm.ollama_client import call_ollama


def create_report(tool_result):

    if not tool_result.get("success"):

        return f"""

Greška prilikom izvršavanja alata:

{tool_result.get("error")}

"""

    tool_name = tool_result.get("tool")
    data = tool_result.get("result")

    if tool_name == "remember_fact":
        return _create_memory_confirmation(data)

    if tool_name == "run_command":
        return _create_command_report(data)

    return _create_system_report(data)


def _create_memory_confirmation(data):
    return f"Zapamtio sam: {data['key']} = {data['value']}"


def _create_command_report(data):
    if not data.get("executed"):
        return data.get("output", "Komanda nije izvršena.")

    status = "uspešno" if data.get("success") else "sa greškom"
    return f"""Komanda `{data['command']}` izvršena {status}.

Izlaz:
{data['output']}"""


def _create_system_report(data):

    prompt = f"""

Ti si SRE inženjer.

Analiziraj sledeći rezultat sistema:

{data}


Napravi kratak profesionalni izveštaj.

Prikaži:

- trenutno stanje sistema
- CPU opterećenje
- memoriju
- disk
- da li postoji problem
- preporuku ako je potrebna


Odgovaraj na srpskom jeziku latinicom.

"""

    return call_ollama(prompt, temperature=0.2, num_predict=200)
