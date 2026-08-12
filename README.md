# VELES — AI Operations Center

**VELES** is an AI-powered Operations Center for **DevOps, SRE and infrastructure operations**.

VELES is being built as a unified operational environment where infrastructure can be discovered, registered, verified, monitored and eventually operated through AI-assisted workflows.

The long-term goal is to move beyond traditional infrastructure tooling toward an **AI-native Operations Center** capable of observing infrastructure, understanding operational state, planning actions, executing controlled operations, verifying results and reporting outcomes.

> **VELES is not just a dashboard, chatbot, monitoring tool or automation script. It is being built as an AI Operations Center.**

---

## Vision

Traditional infrastructure operations require engineers to move between many separate systems:

```text
Monitoring
SSH
Cloud Consoles
Network Tools
Deployment Systems
Logs
Databases
Security Tools
Automation Scripts
AI Assistants
```

VELES aims to bring these operational concerns into one environment:

```text
                    ┌─────────────────────┐
                    │       VELES         │
                    │                     │
                    │  SEE               │
                    │  UNDERSTAND        │
                    │  PLAN              │
                    │  ACT               │
                    │  VERIFY            │
                    │  REPORT            │
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼─────────────────┐
             ▼                 ▼                 ▼
       Infrastructure       AI Core          Operations
             │                 │                 │
             └─────────────────┼─────────────────┘
                               ▼
                         Real Operations
```

The immediate priority is building a **stable operational foundation** on top of which deeper AI reasoning and automation can be developed.

---

# Current Operational Model

The core VELES model is:

```text
Observe
   ↓
Understand
   ↓
Plan
   ↓
Execute
   ↓
Verify
   ↓
Report
```

Not every stage is fully autonomous today.

The current implementation focuses on building the infrastructure, resource, discovery, verification, monitoring and AI foundations required to support this model safely.

---

# Architecture

VELES currently consists of several major layers:

```text
                         ┌──────────────────────┐
                         │      VELES Web UI    │
                         │                      │
                         │ Dashboard            │
                         │ Chat                 │
                         │ Infrastructure       │
                         │ Discovery            │
                         │ Monitoring           │
                         │ System / Services    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      VELES Core      │
                         │                      │
                         │ Brain                │
                         │ Planner              │
                         │ Executor             │
                         │ Reporter             │
                         │ Autonomous           │
                         │ Identity             │
                         └──────────┬───────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                  │
                 ▼                  ▼                  ▼
          ┌────────────┐     ┌────────────┐     ┌────────────┐
          │   Ollama   │     │ PostgreSQL │     │  Modules   │
          │ Local AI   │     │ Operational│     │ Operations │
          │            │     │   State    │     │            │
          └────────────┘     └────────────┘     └──────┬─────┘
                                                       │
                              ┌────────────────────────┼──────────────┐
                              ▼                        ▼              ▼
                       Infrastructure             Discovery       Monitoring
```

---

# AI Core

The AI Core is the intelligence foundation of VELES.

Current core components include:

* Brain
* Planner
* Executor
* Reporter
* Autonomous operations
* Identity
* Operational context
* Memory

The architecture is designed around the idea that AI should eventually understand the operational environment rather than function as an isolated chatbot.

---

# Local AI

VELES supports local LLM inference through **Ollama**.

```text
VELES
  │
  ▼
AI Core
  │
  ▼
Ollama
  │
  ▼
Local LLM
```

Local AI provides a foundation for keeping infrastructure context and operational data inside the VELES environment.

Potential uses include:

* Infrastructure analysis
* Troubleshooting
* Operational planning
* Incident analysis
* Resource understanding
* Command generation
* Operational explanations
* AI-assisted automation

---

# AI Chat

VELES includes an operational AI Chat interface.

The purpose is to connect the operator with the VELES intelligence layer and, progressively, with the operational context managed by VELES.

```text
Operator
   │
   ▼
VELES Chat
   │
   ▼
AI Core
   │
   ├── Memory
   ├── Infrastructure
   ├── Discovery
   └── Operational Context
   │
   ▼
Planner
   │
   ▼
Executor
   │
   ▼
Reporter
```

The long-term goal is for the AI to reason about real infrastructure rather than provide generic answers disconnected from the environment.

---

# Memory

VELES includes a Memory foundation for maintaining operational context.

The Memory layer is intended to support continuity across:

* AI interactions
* Infrastructure knowledge
* Resources
* Operational events
* Previous actions
* System knowledge
* Operational decisions

Memory is part of the foundation for future context-aware AI operations.

---

# Infrastructure

Infrastructure is currently one of the most developed areas of VELES.

The Infrastructure module provides the central operational resource model.

Current capabilities include:

* Resource Registry
* Resource inventory
* Resource identity
* Resource verification
* Resource status
* Infrastructure services
* Discovery integration

Resources are stored in **PostgreSQL** rather than a simple JSON inventory.

A resource can contain:

```text
Resource
├── ID
├── Type
├── Name
├── Host
├── Port
├── Username
├── Group
├── Status
├── Verification
├── Trust
├── Identity
├── Policy
└── Actions
```

---

# Resource Registry

The Resource Registry is the persistent inventory of managed VELES resources.

The registry was migrated from a JSON-based implementation to PostgreSQL.

This provides a stronger foundation for:

* Persistent resource state
* Resource identity
* Verification
* Trust information
* Policies
* Actions
* Future automation

The resource model is intentionally generic so VELES can operate in different environments.

---

# Resource Identity

Managed resources can receive a VELES identity.

Identity information can include:

* Internal UUID
* Version
* Creation timestamp
* Hostname
* Network identity
* Tailscale identity
* Resource-specific identity information

The purpose is to provide a reliable identity layer for future operational reasoning and automation.

---

# Verification

VELES has an explicit resource verification lifecycle.

```text
never_checked
      │
      ▼
   checking
    /    \
   ▼      ▼
verified  failed
```

Verification allows VELES to distinguish between:

* A resource known to the registry
* A reachable resource
* A verified resource
* A resource whose verification failed

This is an important foundation for safe operational actions.

---

# Discovery Center

Discovery is intentionally separated from Infrastructure.

The Discovery Center allows VELES to inspect an environment before resources are imported into the managed infrastructure registry.

```text
Network
   ↓
Discovery
   ↓
Detected Hosts
   ↓
Operator Review
   ↓
ADD RESOURCE
   ↓
Infrastructure Registry
```

Discovery can identify:

* IP addresses
* Hostnames
* Operating systems when available
* Services
* Open ports
* Network targets

Common infrastructure services include:

```text
SSH      22
WinRM    5985
WinRM    5986
RDP      3389
SMB      445
```

## Human-controlled discovery

Discovery does **not** automatically add discovered resources.

The intended workflow is:

> **VELES sees the infrastructure. The operator decides what becomes a managed resource.**

This separation is an important design principle of VELES.

---

# Monitoring

Monitoring is currently under active development.

The current Monitoring foundation includes:

* Health checks
* Resource health
* Connectivity checks
* Health result storage
* Monitoring UI

Conceptually:

```text
Resource
   │
   ▼
Health Check
   │
   ▼
Health Result
   │
   ▼
Resource Health
   │
   ├── VELES UI
   └── AI Context
```

The long-term objective is to make monitoring one of the primary sources of operational context for the AI Core.

---

# Web Operations Center

VELES provides a Flask-based web Operations Center.

Current operational areas include:

* Dashboard
* AI Chat
* Memory
* Logs
* System
* Services
* Infrastructure
* Discovery
* Monitoring

Additional operational domains are planned as the platform develops.

The UI follows a consistent VELES visual language and is designed as a single Operations Center rather than a collection of unrelated pages.

---

# Dashboard

The Dashboard provides the central operational overview.

It is intended to surface:

* Infrastructure state
* Managed resources
* Services
* System information
* Operational information
* AI capabilities

The Dashboard acts as the entry point into the VELES Operations Center.

---

# PostgreSQL

PostgreSQL is the primary application database used by VELES.

It currently provides persistent storage for operational state including managed resources and associated metadata.

The Resource Registry migration from JSON to PostgreSQL is an important architectural step toward making VELES a persistent operational platform.

Example resource fields include:

```text
id
type
name
host
port
username
group
status
created_at
verification
trust
identity
policy
actions
```

---

# Delivery

**Delivery is a planned operational domain of VELES and is currently under development.**

The intended future lifecycle is:

```text
Source
  ↓
Build
  ↓
Test
  ↓
Deploy
  ↓
Verify
  ↓
Monitor
```

The goal is to bring delivery operations into the same operational context as infrastructure, monitoring and AI.

Delivery should not become an isolated deployment system. It is intended to become part of the wider VELES operational lifecycle.

---

# Future Operational Domains

VELES is designed to grow beyond its current Infrastructure, Discovery and Monitoring foundations.

Planned operational domains include:

```text
Infrastructure
Discovery
Monitoring
Delivery
Cloud
Security
Automation
Network
Platform
Data
Testing
```

These domains are part of the long-term architecture and will be implemented incrementally.

They should share a common VELES operational model rather than becoming isolated tools.

---

# Automation

Automation is a major long-term objective.

The intended model is:

```text
AI / Operator
      │
      ▼
    Plan
      │
      ▼
Policy / Approval
      │
      ▼
  Execution
      │
      ▼
 Verification
      │
      ▼
   Reporting
```

Automation should be:

* Observable
* Controlled
* Policy-aware
* Verifiable
* Auditable

VELES is not intended to blindly execute AI-generated infrastructure changes.

---

# Safety and Control

AI-assisted operations should remain controlled.

The intended operational lifecycle is:

```text
Observation
    ↓
Analysis
    ↓
Plan
    ↓
Policy / Approval
    ↓
Execution
    ↓
Verification
    ↓
Report
```

This provides the foundation for future autonomous operations without removing operator control.

---

# Environment Independence

VELES is designed as a **generic infrastructure operations platform**.

Environment-specific information must not be hardcoded into the application.

This includes:

* IP addresses
* Hostnames
* Servers
* Local inventory
* Cloud resources
* Credentials
* Network targets
* User-specific infrastructure

Such information should come dynamically from:

* Configuration
* Discovery
* Resource Registry
* Database
* Runtime environment
* External integrations
* Secret management

This allows VELES to be cloned and deployed into different environments without modifying application source code.

---

# Technology Stack

Current core technologies include:

```text
Python
Flask
PostgreSQL
SQLAlchemy
Ollama
PyTorch
Piper TTS
Linux
Git
```

The project is designed to integrate with common DevOps, SRE, infrastructure and platform technologies as development progresses.

---

# Voice Operations

VELES also has a voice interface direction based on Piper TTS.

The long-term objective is to provide a native voice interface for interacting with VELES.

```text
Operator
    │
    ▼
  VELES
    │
    ├── AI / LLM
    │
    └── TTS
         │
         ▼
      Spoken AI
```

Voice is intended to become another interface to the same VELES operational intelligence.

It is not a separate product from the Operations Center.

---

# Development Philosophy

VELES follows several core principles.

### Generic

VELES should work in different environments without hardcoded infrastructure.

### Modular

Operational domains should remain separated while sharing a common operational model.

### Observable

System state and operations should be visible.

### Verifiable

Operations should be verified rather than assuming success.

### AI-assisted

AI should help operators understand and operate infrastructure.

### Controlled

Automation should respect operational boundaries and policy.

### Incremental

Stable functionality should be preserved while new capabilities are introduced.

### Reusable

Existing stable UI and backend patterns should be reused instead of creating unnecessary parallel implementations.

---

# Repository Structure

A simplified structure:

```text
veles/
│
├── core/
│   ├── brain.py
│   ├── planner.py
│   ├── executor.py
│   ├── reporter.py
│   ├── autonomous.py
│   └── identity.py
│
├── modules/
│   ├── infrastructure/
│   ├── monitoring/
│   └── ...
│
├── web/
│   ├── templates/
│   └── static/
│
├── requirements.txt
└── ...
```

The repository structure is expected to evolve as VELES grows.

---

# Development Status

## Working / Foundation

* Web Operations Center
* Dashboard
* AI Chat
* Memory foundation
* Logs
* System
* Services
* Infrastructure
* PostgreSQL Resource Registry
* Resource Identity
* Resource Verification
* Discovery
* Discovery → operator-controlled resource import
* Monitoring foundation
* Local AI integration
* Piper TTS integration

## Building

* Advanced Monitoring
* Delivery
* Deeper AI operational context
* Operational reasoning
* Expanded resource operations
* AI-assisted operational workflows

## Planned

* Advanced Delivery workflows
* Cloud operations
* Security operations
* Automation engine
* Network operations
* Platform operations
* Data operations
* Testing operations
* Policy-driven execution
* Approval workflows
* Automated remediation
* Continuous verification
* Autonomous operational loops
* Multi-resource reasoning
* Incident response automation
* Full voice-operated VELES

---

# Roadmap

## Phase 1 — Operations Foundation

Build the stable operational foundation.

* Web Operations Center
* Dashboard
* AI Chat
* Memory
* Logs
* System
* Services
* Infrastructure Registry
* PostgreSQL
* Discovery
* Resource Identity
* Resource Verification

**Status: Foundation established and actively evolving.**

---

## Phase 2 — Operational Intelligence

Expand the connection between AI and operational state.

* AI Core
* Brain
* Planner
* Executor
* Reporter
* Local LLM integration
* Infrastructure context
* Operational reasoning
* Incident analysis
* AI-assisted remediation

**Status: In progress.**

---

## Phase 3 — Operations

Expand the operational domains.

* Advanced Monitoring
* Delivery workflows
* Automation
* Network operations
* Security operations
* Cloud operations

**Status: Building / planned incrementally.**

---

## Phase 4 — Autonomous Operations

Move from AI assistance toward controlled autonomous operations.

* Policy-driven execution
* Approval workflows
* Automated remediation
* Continuous verification
* Autonomous operational loops
* Multi-resource reasoning
* Incident response automation

**Status: Future direction.**

---

## Phase 5 — Voice Operations

Extend VELES through voice interaction.

* Piper integration
* Serbian TTS
* Training pipeline
* Final voice model
* Voice interface
* Voice-controlled operations

**Status: Development direction.**

---

# Long-Term Architecture

The long-term VELES architecture is intended to converge toward:

```text
                         ┌───────────────────────┐
                         │        VELES          │
                         │  AI Operations Center │
                         └───────────┬───────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
       Infrastructure            AI Core               Operations
              │                      │                      │
       ┌──────┼──────┐               │          ┌───────────┼───────────┐
       ▼      ▼      ▼               ▼          ▼           ▼           ▼
    Hosts   Network  Cloud        Reasoning  Monitor     Delivery   Automation
       │      │      │               │          │           │           │
       └──────┴──────┴───────────────┼──────────┴───────────┴───────────┘
                                     │
                                     ▼
                              Operational State
                                     │
                                     ▼
                              Observe → Act → Verify
```

The architecture is intentionally being built incrementally.

---

# What VELES Is Becoming

VELES is evolving toward a system that can continuously connect:

```text
Infrastructure
       +
Discovery
       +
Identity
       +
Verification
       +
Monitoring
       +
Memory
       +
AI Reasoning
       +
Delivery
       +
Automation
```

The objective is not to build independent tools for each category.

The objective is to build **one operational system that understands the relationships between them**.

---

# Vision

The long-term vision is an Operations Center where an engineer can ask:

```text
What is happening?
        ↓
Why is it happening?
        ↓
What is affected?
        ↓
What are my options?
        ↓
What should we do?
        ↓
Execute the approved action.
        ↓
Did it work?
        ↓
What changed?
```

VELES should progressively turn these questions into an operational feedback loop.

```text
                 ┌───────────────┐
                 │    OBSERVE    │
                 └───────┬───────┘
                         │
                         ▼
                 ┌───────────────┐
                 │   UNDERSTAND  │
                 └───────┬───────┘
                         │
                         ▼
                 ┌───────────────┐
                 │     PLAN      │
                 └───────┬───────┘
                         │
                         ▼
                 ┌───────────────┐
                 │    EXECUTE    │
                 └───────┬───────┘
                         │
                         ▼
                 ┌───────────────┐
                 │    VERIFY     │
                 └───────┬───────┘
                         │
                         ▼
                 ┌───────────────┐
                 │    REPORT     │
                 └───────┬───────┘
                         │
                         └──────────────► OBSERVE
```

---

# Project Direction

The direction of VELES is:

**AI + Infrastructure + Operations + Automation + Voice**

The immediate priority is not to claim autonomous infrastructure management before the underlying systems are ready.

The priority is to build the operational foundation correctly:

```text
Stable Foundation
       ↓
Operational Context
       ↓
AI Understanding
       ↓
Controlled Actions
       ↓
Verification
       ↓
Automation
       ↓
Autonomous Operations
```

That foundation is what will allow VELES to evolve from an AI-assisted Operations Center into a genuinely **AI-native Operations Center**.

---

# Status

VELES is an actively developed project.

The project is currently focused on strengthening the operational foundation around:

* Infrastructure
* Resource Registry
* Discovery
* Identity
* Verification
* Monitoring
* AI Core
* Local AI
* Web Operations Center
* PostgreSQL

The next stages expand these foundations into deeper operational intelligence, delivery, automation and eventually controlled autonomous operations.

> **VELES is being built as an AI Operations Center for real infrastructure operations.**
