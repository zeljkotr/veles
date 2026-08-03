# Veles

Minimalni self-hosted DevOps agent: lokalni LLM (preko Ollama-e) + registar alata
za samo-proveru sistema, sa audit logom i whitelist-om koji sprečava agenta da
sam izvrši rizične akcije bez tvoje potvrde.

## Struktura

```
main.py                     CLI ulazna tačka
veles/
  config.py                 endpoint, model, whitelist bezbednih akcija
  llm_client.py             HTTP klijent za Ollama OpenAI-kompatibilni API
  audit.py                  SQLite audit log + gate za potvrdu rizičnih akcija
  agent.py                  ReAct petlja (poziv modela -> tool_calls -> izvršenje -> nazad modelu)
  tools/
    __init__.py              registar: ime alata -> (funkcija, JSON schema)
    dtool_bridge.py           poziva postojeće dtool monitoring funkcije (ping/http/ssl)
    system_checks.py          novi alati: disk, systemctl, docker, journalctl, restart
```

## Kako radi bezbednosna kapija

`config.safe_tools` su alati koji se izvršavaju odmah (svi su read-only: provere
diska, statusa servisa, docker containera, skeniranje logova). Sve što menja
stanje sistema (`restart_service`, `restart_docker_container`) NIJE na toj listi
— čak i ako model to pozove, `agent.py` to samo upisuje u `audit.py` kao
`pending_confirmation` i ne izvršava ništa dok ti eksplicitno ne odobriš:

```bash
python main.py --pending           # vidi šta čeka odobrenje
python main.py --approve 3         # odobri i izvrši poziv #3
python main.py --reject 3          # odbij poziv #3
```

## Kad stigne LOQ

Ništa u kodu se ne menja — samo env promenljive:

```bash
export VELES_OLLAMA_HOST="http://<loq-tailscale-ip>:11434"
export VELES_MODEL="qwen3:8b"
python main.py "proveri disk i status nginx servisa"
```

Dok testiraš bez GPU-a, ostavi podrazumevano (`http://localhost:11434`,
manji model) — čim `ollama pull qwen3:8b` završi na LOQ-u, samo promeniš dve
promenljive.

## Povezivanje sa pravim dtool-om

`veles/tools/dtool_bridge.py` trenutno koristi mock rezultate jer imena
funkcija (`ping`, `http_status`, `ssl_expiry`) u komentaru su pretpostavka —
otvori `~/vezbe/dtools/modules/monitoring/core.py` i uskladi import imena i
potpise funkcija sa stvarnim kodom. Kad se `from modules.monitoring.core import ...`
uspešno izvrši, `DTOOL_AVAILABLE` postaje `True` i pravi rezultati zamenjuju mock.

## Dodavanje novog alata

1. Napiši funkciju u `system_checks.py` (ili novi fajl u `tools/`).
2. Registruj je u `tools/__init__.py` — ime, funkcija, JSON schema parametara.
3. Ako menja stanje sistema, dodaj ime u `config.confirmation_required`.

Ništa drugo ne treba menjati — `agent.py` i `main.py` rade sa bilo kojim brojem
alata iz registra.

## Sledeći koraci (nisu u ovoj verziji)

- Memorija (SQLite + embeddings) za pamćenje prošlih incidenata
- Web dashboard (Flask, u stilu dtool-a) umesto CLI-ja
- Glasovni sloj (whisper.cpp STT, XTTS TTS) kad LOQ stigne
