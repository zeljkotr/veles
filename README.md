# Veles

Minimalni self-hosted DevOps agent: lokalni LLM (preko Ollama-e) + registar alata
za samo-proveru sistema, sa audit logom i whitelist-om koji sprečava agenta da
sam izvrši rizične akcije bez tvoje potvrde.

## Struktura
=======
The goal of Veles is not only to answer questions, but to understand tasks, execute actions, analyze results and help with system administration, automation and infrastructure operations.

---

# Why the name Veles?

The name Veles comes from Slavic mythology.

Veles (Велес) was one of the most important ancient Slavic gods, associated with wisdom, knowledge, magic, nature, earth, wealth and the unseen world.

In Slavic tradition, Veles represents intelligence, adaptability and the ability to understand hidden connections.

The project name was chosen because the goal of this AI assistant is similar:

- to collect knowledge
- to understand complex systems
- to connect information
- to help with decisions
- to work alongside humans

Veles is not designed as a simple chatbot.

The vision is to build an intelligent technical companion capable of assisting with:

- SRE operations
- DevOps workflows
- infrastructure management
- automation
- system analysis

The name represents the idea of combining ancient symbolism of knowledge and modern artificial intelligence.

---

# Vision

Veles is built as a modular AI agent architecture.

The idea is to create a local Jarvis-like assistant that can work as an infrastructure engineer:

- monitor systems
- execute tools
- analyze problems
- automate tasks
- maintain knowledge
- assist with DevOps/SRE operations

Architecture:

```
User
 |
 v
Brain
 |
 v
Planner
 |
 v
Executor
 |
 v
Tools
 |
 v
Reporter
 |
 v
Response
```

---

# Current Features

## AI Brain

- Local LLM integration using Ollama
- Qwen2.5 7B model support
- Serbian Latin language support
- Custom personality system
- Memory integration

---

## Planner

Planner decides what action should happen.

Examples:

```
proveri sistem

proveri mi server

daj mi stanje računara

mozes li da proveris server
```

Example output:

```json
{
    "action": "system_info"
}
```

---

## Executor

Executor is the action layer.

It receives commands from the planner and executes available tools.

Current tools:

```
system_info
```

Executor provides:

- tool validation
- execution control
- error handling
- structured results

---

## System Tool

Current system monitoring capabilities:

- Hostname
- Operating system
- CPU usage
- Memory usage
- Disk usage

Example result:

```json
{
    "hostname": "meshcorers",
    "os": "Linux",
    "cpu_usage": "1%",
    "memory_percent": "20%",
    "disk_free": "800GB"
}
```

---

## Reporter

Reporter converts tool results into readable reports.

Example:

```
Izvršena je provera sistema.

Server:
meshcorers

CPU:
1%

Memorija:
20%

Disk:
800GB slobodno

Status:
Sistem radi normalno.
```

---

# Project Structure

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
