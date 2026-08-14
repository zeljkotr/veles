# ⚡ VELES

### Local AI Operations Center for DevOps, SRE & Infrastructure

> **Understand. Discover. Monitor. Analyze. Operate.**

VELES is a self-hosted AI Operations platform designed to help engineers understand, monitor and operate infrastructure.

It combines **local AI, infrastructure management, network discovery, monitoring, security and automation** into a single operational environment.

VELES is not designed to be just a chatbot.

The goal is to build an intelligent technical companion capable of understanding operational tasks, inspecting infrastructure, analyzing results and helping humans safely operate real systems.

---

## 🚀 Project Status

| Module             |       Status      |
| ------------------ | :---------------: |
| 🧠 Intelligence    | 🟡 IN DEVELOPMENT |
| 🏗️ Infrastructure |     🟢 ACTIVE     |
| 🔎 Discovery       |     🟢 ACTIVE     |
| 📊 Monitoring      |     🟢 ACTIVE     |
| 🛡️ Security       | 🟡 IN DEVELOPMENT |
| 🌐 Network         | 🟡 IN DEVELOPMENT |
| 🚚 Delivery        | 🟡 IN DEVELOPMENT |
| ☁️ Cloud           |     ⚪ PLANNED     |
| ⚙️ Automation      |     ⚪ PLANNED     |
| 🖥️ Platform       |     ⚪ PLANNED     |
| 💾 Data            |     ⚪ PLANNED     |
| 🧪 Testing         |     ⚪ PLANNED     |

### Status

* 🟢 **ACTIVE** — Functional and operational
* 🟡 **IN DEVELOPMENT** — Currently being developed
* ⚪ **PLANNED** — Planned for a future phase

---

# ✅ Completed Foundation

The following VELES foundation components are completed:

| Component                    |    Status    |
| ---------------------------- | :----------: |
| PostgreSQL                   | 🟢 COMPLETED |
| Resource Registry            | 🟢 COMPLETED |
| Infrastructure Module        | 🟢 COMPLETED |
| Network Discovery            | 🟢 COMPLETED |
| Host Discovery               | 🟢 COMPLETED |
| Port Discovery               | 🟢 COMPLETED |
| Service Discovery            | 🟢 COMPLETED |
| Manual Resource Registration | 🟢 COMPLETED |
| Monitoring Foundation        | 🟢 COMPLETED |
| Monitoring UI                | 🟢 COMPLETED |
| Security Foundation          | 🟢 COMPLETED |

This foundation provides the infrastructure layer on which the higher-level VELES Intelligence and Automation capabilities are being built.

---

# 🎯 What Is VELES?

Traditional AI assistants usually follow a simple model:

```text
User
  ↓
Question
  ↓
LLM
  ↓
Answer
```

VELES is designed around an operational model:

```text
User
  ↓
Understand
  ↓
Plan
  ↓
Discover / Inspect
  ↓
Execute
  ↓
Analyze
  ↓
Report
  ↓
Human
```

The long-term goal is for VELES to understand not only what the user asks, but also what needs to be done inside the infrastructure.

For example:

```text
"Check the server and find out why nginx is not working."
```

VELES should eventually be able to:

1. Identify the target resource
2. Check resource health
3. Inspect system state
4. Check nginx
5. Inspect relevant logs
6. Correlate the results
7. Determine the likely problem
8. Explain the problem
9. Recommend an action
10. Request confirmation before changing system state

---

# 🧠 Intelligence Architecture

VELES follows a modular AI-agent architecture.

```text
                         ┌───────────────────┐
                         │       USER        │
                         └─────────┬─────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │       BRAIN       │
                         │    Local LLM      │
                         └─────────┬─────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │      PLANNER      │
                         │   Task Analysis   │
                         └─────────┬─────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │     EXECUTOR      │
                         │ Tool Orchestration │
                         └─────────┬─────────┘
                                   │
             ┌─────────────────────┼─────────────────────┐
             │                     │                     │
             ▼                     ▼                     ▼
      Infrastructure          Monitoring             Security
      Discovery / Registry     Health Checks          Inspection
             │                     │                     │
             └─────────────────────┼─────────────────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │     REPORTER      │
                         │ Analysis / Result │
                         └─────────┬─────────┘
                                   │
                                   ▼
                                USER
```

---

# 🧩 VELES Modules

VELES is organized as a modular operations platform.

```text
Intelligence
Infrastructure
Delivery
Cloud
Security
Automation
Monitoring
Network
Platform
Data
Testing
```

Each module has a specific responsibility and can evolve independently.

---

# 🏗️ Infrastructure

Infrastructure is the foundation of VELES.

The module provides a centralized **Resource Registry** backed by PostgreSQL.

Resources can represent:

* Linux servers
* Windows systems
* virtual machines
* containers
* network devices
* services
* infrastructure endpoints

The Resource Registry provides a consistent identity that other VELES modules can use.

```text
                    PostgreSQL
                        │
                        ▼
                ┌───────────────┐
                │    Resource   │
                │    Registry   │
                └───────┬───────┘
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
      Discovery     Monitoring     Security
          │             │             │
          └─────────────┼─────────────┘
                        ▼
                   VELES AI
```

---

# 🔎 Discovery

Discovery allows VELES to understand infrastructure before resources are registered.

The discovery pipeline is:

```text
Network Targets
      │
      ▼
Network Discovery
      │
      ▼
Live Hosts
      │
      ▼
Ports
      │
      ▼
Services
      │
      ▼
Version / OS Detection
      │
      ▼
Discovery Results
      │
      ▼
  ADD RESOURCE
      │
      ▼
Resource Registry
```

Discovery does **not** automatically register everything it finds.

The operator decides which discovered systems should become managed resources.

This creates a clear separation between:

**Discovery → Verification → Registration**

---

# 📊 Monitoring

Monitoring provides health information for registered resources.

Current monitoring capabilities include:

* resource health checks
* ping checks
* response-time measurement
* health status
* monitoring results
* monitoring UI

The architecture is designed to support additional checks such as:

* HTTP
* SSL
* service status
* Docker
* system resources
* logs

Example health result:

```json
{
  "resource_id": "6",
  "check_type": "ping",
  "status": "healthy",
  "response_time": 12.4
}
```

Monitoring results can become input for the Intelligence layer.

---

# 🛡️ Security

Security is designed as a dedicated inspection layer.

The architecture separates:

```text
LOCAL SECURITY
      +
REMOTE SECURITY
```

The initial security model focuses on read-only inspection such as:

* system state
* users
* services
* listening ports
* processes
* filesystem information
* security-related configuration

The Security module is designed to inspect infrastructure without silently modifying it.

---

# 🌐 Network

Network provides network-level visibility and operational capabilities.

The module works together with Discovery and Infrastructure to build a better understanding of:

```text
Networks
   ↓
Hosts
   ↓
Ports
   ↓
Services
   ↓
Resources
```

The long-term goal is to allow VELES to understand infrastructure relationships rather than treating every host as an isolated object.

---

# 🔐 Safety Model

VELES is designed around **human-controlled operations**.

AI reasoning and system-changing actions are deliberately separated.

Read-only operations can execute automatically.

Examples:

```text
system_info
disk_usage
service_status
docker_status
journal_logs
ping
http_status
ssl_expiry
```

Operations that modify system state require explicit approval.

Examples:

```text
restart_service
restart_docker_container
```

Execution flow:

```text
                  AI
                   │
                   ▼
              Tool Request
                   │
                   ▼
              Safety Gate
                   │
          ┌────────┴────────┐
          │                 │
          ▼                 ▼
        SAFE          APPROVAL REQUIRED
          │                 │
          ▼                 ▼
       Execute          Audit Log
                              │
                       ┌──────┴──────┐
                       ▼             ▼
                    APPROVE        REJECT
                       │
                       ▼
                    Execute
```

The AI cannot bypass this boundary simply by generating a tool request.

---

# 🧰 Tool Architecture

VELES uses a registry-based tool architecture.

Each tool exposes:

* unique name
* implementation
* parameter schema
* structured result
* validation
* error handling

Example tools:

```text
system_info
disk_usage
service_status
docker_status
journal_logs
ping
http_status
ssl_expiry
```

The architecture allows new tools to be added without rewriting the Planner or Executor.

---

# 🗄️ PostgreSQL

VELES uses PostgreSQL as the persistent state database.

The database provides storage for infrastructure and operational state such as:

* resources
* resource metadata
* health state
* verification data
* monitoring information
* operational history

Database configuration is externalized.

Credentials and secrets should never be hardcoded into the source tree.

---

# 🖥️ Web Operations Center

VELES includes a Flask-based web interface.

The interface brings the major operational modules together:

```text
┌──────────────────────────────────────────────────────────┐
│                         VELES                            │
├───────────────┬──────────────────────────────────────────┤
│               │                                          │
│ Dashboard     │              Operations Center           │
│               │                                          │
│ Chat          │   Resources     Monitoring     Security  │
│               │                                          │
│ Infrastructure│   Discovery     Network        Logs      │
│               │                                          │
│ Discovery     │                                          │
│               │                                          │
│ Monitoring    │                                          │
│               │                                          │
│ Security      │                                          │
│               │                                          │
└───────────────┴──────────────────────────────────────────┘
```

The UI follows a consistent design language across modules so that VELES behaves like a single Operations Center.

---

# 🤖 Local AI

VELES uses Ollama for local LLM inference.

This allows AI processing to remain under the operator's control.

Example configuration:

```bash
export VELES_OLLAMA_HOST="http://localhost:11434"
export VELES_MODEL="qwen3:8b"
```

The AI backend can also be hosted on another machine:

```bash
export VELES_OLLAMA_HOST="http://<remote-host>:11434"
export VELES_MODEL="qwen3:8b"
```

No application code needs to change when moving the LLM backend.

---

# 💻 CLI

VELES can also be operated from the command line.

Example:

```bash
python main.py "check disk usage and nginx status"
```

Pending operations:

```bash
python main.py --pending
```

Approve an operation:

```bash
python main.py --approve 3
```

Reject an operation:

```bash
python main.py --reject 3
```

The CLI remains useful for:

* debugging
* administration
* automation
* development
* environments without the web interface

---

# 📁 Project Structure

```text
veles/
│
├── main.py
│
├── veles/
│   │
│   ├── config.py
│   ├── llm_client.py
│   ├── agent.py
│   ├── audit.py
│   │
│   ├── web/
│   │   └── app.py
│   │
│   ├── modules/
│   │   ├── intelligence/
│   │   ├── infrastructure/
│   │   ├── monitoring/
│   │   ├── network/
│   │   ├── security/
│   │   ├── delivery/
│   │   ├── cloud/
│   │   ├── automation/
│   │   ├── platform/
│   │   ├── data/
│   │   └── testing/
│   │
│   └── tools/
│       ├── __init__.py
│       ├── dtool_bridge.py
│       └── system_checks.py
│
├── requirements.txt
├── install.sh
└── README.md
```

---

# 🔄 Operational Workflow

A typical VELES workflow looks like this:

```text
┌──────────────┐
│     User     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Understand  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│     Plan     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Inspect /    │
│ Discover     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    Execute   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    Analyze   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    Report    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    Human     │
└──────────────┘
```

---

# 🗺️ Roadmap

## Phase 1 — Foundation

| Component                    |    Status    |
| ---------------------------- | :----------: |
| PostgreSQL                   | 🟢 COMPLETED |
| Resource Registry            | 🟢 COMPLETED |
| Infrastructure Module        | 🟢 COMPLETED |
| Network Discovery            | 🟢 COMPLETED |
| Host Discovery               | 🟢 COMPLETED |
| Port Discovery               | 🟢 COMPLETED |
| Service Discovery            | 🟢 COMPLETED |
| Manual Resource Registration | 🟢 COMPLETED |
| Monitoring Foundation        | 🟢 COMPLETED |
| Monitoring UI                | 🟢 COMPLETED |
| Security Foundation          | 🟢 COMPLETED |

## Phase 2 — Intelligence

| Component              |       Status      |
| ---------------------- | :---------------: |
| Ollama Integration     |    🟢 COMPLETED   |
| Local LLM              |    🟢 COMPLETED   |
| AI Chat                |    🟢 COMPLETED   |
| Advanced Planner       | 🟡 IN DEVELOPMENT |
| Tool Orchestration     | 🟡 IN DEVELOPMENT |
| Persistent Memory      |     ⚪ PLANNED     |
| Incident Analysis      |     ⚪ PLANNED     |
| AI-Assisted Monitoring |     ⚪ PLANNED     |

## Phase 3 — Operations

| Component              |   Status  |
| ---------------------- | :-------: |
| Advanced Health Checks | ⚪ PLANNED |
| Alerting               | ⚪ PLANNED |
| Event Correlation      | ⚪ PLANNED |
| Incident Workflows     | ⚪ PLANNED |
| Automation             | ⚪ PLANNED |
| Remote Execution       | ⚪ PLANNED |
| Controlled Remediation | ⚪ PLANNED |

## Phase 4 — Platform

| Component                 |   Status  |
| ------------------------- | :-------: |
| Cloud Integrations        | ⚪ PLANNED |
| Docker Operations         | ⚪ PLANNED |
| Kubernetes                | ⚪ PLANNED |
| Infrastructure Automation | ⚪ PLANNED |
| Advanced SRE Workflows    | ⚪ PLANNED |
| Multi-Agent Capabilities  | ⚪ PLANNED |
| Voice Interface           | ⚪ PLANNED |

---

# 🧭 Long-Term Vision

VELES is moving toward an **AI Operations Center** rather than a traditional AI assistant.

```text
                       ┌────────────────────┐
                       │       VELES        │
                       │  AI OPERATIONS     │
                       │      CENTER        │
                       └─────────┬──────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
        Intelligence       Infrastructure        Security
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 │
                                 ▼
                            Monitoring
                                 │
                                 ▼
                            Automation
                                 │
                                 ▼
                         Operational AI
                                 │
                                 ▼
                       Controlled SRE
```

The objective is not uncontrolled autonomy.

The objective is **useful, observable and human-controlled automation**.

---

# 🧙 Why Veles?

The name **Veles (Велес)** comes from Slavic mythology.

Veles was one of the major Slavic deities associated with:

* wisdom
* knowledge
* magic
* nature
* earth
* wealth
* the unseen world

The name was chosen because these ideas closely reflect the purpose of the project.

Modern VELES is designed to:

* collect knowledge
* understand complex systems
* connect information
* discover hidden relationships
* assist with decisions
* work alongside humans

In the same way that Veles represents knowledge, adaptability and the unseen world in Slavic tradition, VELES is intended to understand the systems and relationships that are not immediately visible to the engineer.

The name represents the combination of **ancient symbolism of knowledge with modern artificial intelligence**.

---

# 🛠️ Development Philosophy

VELES is developed incrementally.

The project does not attempt to build the entire AI Operations platform at once.

The architecture evolves through layers:

```text
Tools
  ↓
Infrastructure
  ↓
Discovery
  ↓
Monitoring
  ↓
Security
  ↓
Intelligence
  ↓
Automation
  ↓
AI Operations Center
```

Each layer should become reliable before higher-level capabilities depend on it.

This keeps VELES understandable, testable and maintainable.

---

# 🔒 Security Principles

VELES follows several important security principles:

* No hardcoded credentials
* No hardcoded infrastructure identities
* Read-only inspection wherever possible
* Explicit approval for dangerous operations
* Auditability of operational actions
* Separation between AI reasoning and execution
* External configuration for environment-specific values
* Human control over state-changing operations

---

# 📌 Current Direction

VELES is evolving from:

```text
AI Assistant
```

into:

```text
AI Infrastructure Engineer
```

and ultimately:

```text
Local AI Operations Center
```

The final system should be able to understand infrastructure, observe its state, investigate problems, correlate information and assist with real operational work.

---

# ⭐ The Goal

The goal of VELES is not simply to answer questions.

The goal is to create a system that can:

```text
UNDERSTAND
     ↓
DISCOVER
     ↓
MONITOR
     ↓
ANALYZE
     ↓
PLAN
     ↓
EXECUTE
     ↓
VERIFY
     ↓
REPORT
```

while keeping the human engineer in control of critical actions.

---

## ⚡ VELES

**Local intelligence for real infrastructure.**

Built for **DevOps. SRE. Infrastructure. Operations.**
