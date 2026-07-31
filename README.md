# veles
Personal Ai project aiming wingman capabilities
# Veles AI Assistant

Veles is a local AI assistant designed as a personal SRE/DevOps worker.

The goal of Veles is not only to answer questions, but to understand tasks, execute actions, analyze results and help with system administration, automation and infrastructure operations.

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
veles/

├── main.py
├── requirements.txt
├── README.md
│
├── veles/
│   │
│   ├── core/
│   │   ├── brain.py
│   │   ├── planner.py
│   │   ├── executor.py
│   │   └── reporter.py
│   │
│   ├── tools/
│   │   └── system.py
│   │
│   ├── personality/
│   │   └── personality.py
│   │
│   ├── memory/
│   │   └── memory.py
│   │
│   ├── knowledge/
│   │
│   ├── plugins/
│   │
│   ├── stt/
│   │
│   └── tts/
│
└── venv/
```

---

# Installation

Clone repository:

```bash
git clone https://github.com/zeljkotr/veles.git
```

Enter directory:

```bash
cd veles
```

Create virtual environment:

```bash
python3 -m venv venv
```

Activate environment:

Linux:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# Requirements

System:

- Linux
- Python 3.14+
- Ollama
- Local LLM model


Install Ollama model:

```bash
ollama pull qwen2.5:7b
```

---

# Running

Start Veles:

```bash
python main.py
```

Example:

```
====================
     VELES ONLINE
====================

TI: proveri sistem

PLAN:
{
'action': 'system_info'
}

VELES:

Izvršena je provera sistema.

Hostname:
meshcorers

CPU:
1%

RAM:
20%

Status:
Sistem radi normalno.
```

---

# Roadmap

## Phase 1 - Core Agent

[x] Brain

[x] Personality

[x] Planner

[x] Executor

[x] System tools

[x] Reporter


---

## Phase 2 - Knowledge System

[ ] Local knowledge base

[ ] Documentation search

[ ] RAG system

[ ] Linux knowledge

[ ] Docker knowledge

[ ] Kubernetes knowledge


---

## Phase 3 - Infrastructure Automation

[ ] Docker management

[ ] Kubernetes tools

[ ] Log analysis

[ ] Network diagnostics

[ ] Monitoring integration


---

## Phase 4 - Voice Assistant

[ ] Speech-to-text

[ ] Text-to-speech

[ ] Wake word detection

[ ] Voice commands


---

## Phase 5 - Autonomous SRE Agent

[ ] Incident detection

[ ] Automatic diagnosis

[ ] Problem analysis

[ ] Recommendations

[ ] Memory improvement


---

# Philosophy

Veles follows the SRE mindset:

```
Observe
   |
Understand
   |
Test
   |
Automate
   |
Improve
```

The assistant should not only answer questions.

It should work.

---

# Author

Created by Željko Tripčevski

Project:

https://github.com/zeljkotr/veles
