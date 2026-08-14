# VELES — AI Operations Center

VELES is an AI-powered Operations Center for DevOps, SRE and infrastructure operations.

The goal of VELES is to provide a single operational environment for:

- Infrastructure
- Discovery
- Monitoring
- Network Operations
- Security
- Delivery
- Automation
- Cloud Operations
- Platform Operations
- Data Operations
- Testing
- AI-assisted Operations

VELES is being built as an AI-native Operations Center, not simply as a dashboard, chatbot, monitoring tool or automation script.

---

# Vision

VELES is designed around a continuous operational lifecycle:

OBSERVE
↓
UNDERSTAND
↓
PLAN
↓
EXECUTE
↓
VERIFY
↓
REPORT
↓
OBSERVE

The long-term goal is for VELES to understand infrastructure state, provide operational context, assist engineers with decisions, execute approved actions and verify the results.

---

# Current Module Status

| Module | Current State | Status |
|---|---|---|
| 🧠 Intelligence | AI / Chat + Ollama integration | 🟡 Developing |
| 🖥 Infrastructure | Resource Registry + PostgreSQL + Resources + Discovery integration | 🟢 Highly Developed |
| 🔎 Discovery | Network discovery → Hosts → Ports / Services → Add Resource | 🟢 Functional |
| 📊 Monitoring | Monitoring Center + Scheduler + Health Checks + Automatic Cycles | 🟢 Functional / Phase 1 |
| 🌐 Network | Basic Network module | 🟡 Basic |
| 🚚 Delivery | Basic Delivery module | 🟡 Basic |
| 🔐 Security | Local Security / read-only inspection | 🟡 Phase 1 |
| ☁ Cloud | No full module yet | 🔴 Planned |
| ⚙ Automation | No full module yet | 🔴 Planned |
| 🧩 Platform | No full module yet | 🔴 Planned |
| 💾 Data | No full module yet | 🔴 Planned |
| 🧪 Testing | No full module yet | 🔴 Planned |

### Status Legend

- 🟢 Functional / actively usable
- 🟡 Development in progress
- 🔴 Planned

---

# Architecture

                         ┌──────────────────────────┐
                         │          VELES           │
                         │    AI Operations Center  │
                         └────────────┬─────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
              ▼                       ▼                       ▼
       ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
       │   Web UI    │        │ Intelligence│        │ Operations  │
       │   Flask     │        │ AI / Ollama │        │   Modules   │
       └──────┬──────┘        └──────┬──────┘        └──────┬──────┘
              │                       │                       │
              └───────────────────────┼───────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
             Infrastructure      PostgreSQL       External Systems
                    │
          ┌─────────┼─────────┐
          │         │         │
          ▼         ▼         ▼
      Discovery Monitoring Network

---

# Infrastructure

Infrastructure is currently one of the most developed VELES modules.

It provides the operational resource foundation used by other modules.

Current capabilities include:

- Resource Registry
- PostgreSQL-backed resource storage
- Resource inventory
- Resource identity
- Resource verification
- Resource status
- Infrastructure UI
- Integration with Discovery
- Integration with Monitoring

The basic architecture is:

InfrastructureService
        ↓
ResourceRegistry
        ↓
PostgreSQL

Discovery does not automatically register resources.

The operator chooses:

Discovery
    ↓
ADD RESOURCE
    ↓
Resource Registry

VELES must not hardcode infrastructure belonging to a specific user or environment.

IP addresses, hostnames, credentials and other environment-specific values must come from configuration, discovery, the registry, the database or the runtime environment.

---

# Discovery

Discovery is intentionally separated from Infrastructure.

Discovery observes the environment and presents discovered systems to the operator.

The workflow is:

Network
   ↓
Discovery
   ↓
Detected Hosts
   ↓
Ports / Services
   ↓
Operator Review
   ↓
ADD RESOURCE
   ↓
Infrastructure Resource Registry

Discovery does not automatically register every discovered system.

The operator decides which discovered systems become managed VELES resources.

Current discovery capabilities include:

- Network target detection
- Host discovery
- IP detection
- Hostname detection when available
- Open port detection
- Service detection
- Operating system detection when available
- Operator-controlled resource import

Common discovery ports include:

- SSH — 22
- WinRM — 5985
- WinRM — 5986
- RDP — 3389
- SMB — 445

Discovery must remain environment-independent and must not hardcode interfaces, IP addresses or hostnames.

---

# Monitoring

Monitoring is currently in its first functional phase.

The Monitoring Center provides centralized resource health information.

Current capabilities include:

- Resource health checks
- Health status
- Ping checks
- Response time
- Health messages
- Check counts
- Last check information
- Automatic monitoring cycles
- Monitoring scheduler
- Configurable check interval
- Monitoring statistics
- Automatic UI refresh
- Next-check countdown
- Resource monitoring status

The current architecture is:

MonitoringScheduler
        ↓
MonitoringService
        ↓
check_resources()
        ↓
ResourceHealth
        ↓
Monitoring UI

The current automatic check interval is:

60 seconds

Health status priority is:

CRITICAL
   ↓
WARNING
   ↓
UNKNOWN
   ↓
HEALTHY

The monitoring models currently include:

HealthCheckResult
ResourceHealth
MonitoringTarget

Persistent long-term monitoring history in PostgreSQL is planned for a later phase.

---

# Monitoring Scheduler

The Monitoring Scheduler provides automatic periodic monitoring.

It tracks:

- Last check time
- Next check time
- Check count
- Last resource count
- Healthy resources
- Warning resources
- Critical resources
- Unknown resources

The operational cycle is:

MonitoringScheduler
        ↓
Wait
        ↓
Check Resources
        ↓
Collect Health Results
        ↓
Update Monitoring State
        ↓
Update UI
        ↓
Wait
        ↓
Next Cycle

Example:

[MONITORING] Check cycle: 19 resources

[MONITORING] Check cycle complete:
healthy=19 warning=0 critical=0 unknown=0

[MONITORING] Waiting 60 seconds...

---

# Security

Security is currently in its first phase.

The current direction is a read-only local security inspection layer.

The principle is:

VELES should observe and report security state before it performs security-changing operations.

Current direction includes:

- Local security inspection
- System security information
- Read-only checks
- Security status reporting

Future Security capabilities are expected to include:

- Security posture
- Identity
- Access
- Configuration inspection
- Security events
- Resource security state
- Security automation

---

# Intelligence

The Intelligence module connects VELES with local AI capabilities.

VELES currently supports local LLM operation through Ollama.

The intended architecture is:

VELES
  ↓
AI Core
  ↓
Ollama
  ↓
Local LLM

The AI layer is intended to become aware of operational context such as:

- Infrastructure
- Resources
- Discovery
- Monitoring
- Memory
- Operational events

The long-term objective is AI-assisted operational reasoning rather than generic chatbot functionality.

---

# AI Chat

VELES provides an AI Chat interface inside the Operations Center.

The intended operational direction is:

Operator
   ↓
VELES Chat
   ↓
AI Intelligence
   ↓
Operational Context
   ↓
Analysis / Planning
   ↓
Approved Action
   ↓
Verification
   ↓
Report

AI operations are intended to remain controlled and observable.

---

# Network

The Network module currently provides a basic foundation for network operations.

Its long-term purpose is to connect:

- Network resources
- Discovery
- Infrastructure
- Monitoring
- Security
- AI analysis

into a common operational model.

---

# Delivery

Delivery currently provides a basic foundation for deployment-oriented operations.

The long-term workflow is:

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

The module is currently in an early development stage.

---

# Planned Modules

The following modules are part of the VELES architecture but are not yet implemented as full operational modules.

## Cloud

Planned areas:

- Cloud resources
- Compute
- Networking
- Storage
- Cloud services
- Cloud operations
- Cloud automation

## Automation

Planned areas:

- Operational workflows
- Approved execution
- Automation policies
- Verification
- Remediation
- Repeatable operations

## Platform

Planned areas:

- Containers
- Platform services
- Application platforms
- Infrastructure platforms
- Service operations

## Data

Planned areas:

- Data infrastructure
- Databases
- Data services
- Operational data visibility
- Data operations

## Testing

Testing will become part of the complete operational lifecycle:

Develop
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

---

# Web Operations Center

VELES provides a Flask-based web Operations Center.

Current areas include:

- Dashboard
- AI Chat
- Memory
- Logs
- System
- Services
- Infrastructure
- Discovery
- Monitoring
- Delivery

The UI follows a common VELES visual language.

The goal is to provide one coherent Operations Center instead of a collection of unrelated interfaces.

---

# PostgreSQL

VELES uses PostgreSQL as its application database.

The Resource Registry uses PostgreSQL for persistent resource management.

The database provides the foundation for:

- Managed resources
- Resource metadata
- Verification state
- Operational state
- Future persistent monitoring history
- Future operational events

Credentials and environment-specific database configuration must never be hardcoded into the source code.

---

# Environment Independence

VELES is designed to be deployable into different environments.

The application must not hardcode:

- IP addresses
- Hostnames
- Servers
- Credentials
- Network interfaces
- Local inventory
- Cloud resources
- User-specific infrastructure

Environment-specific information should come from:

- Configuration
- Discovery
- Resource Registry
- PostgreSQL
- Runtime environment
- External integrations

This is a core architectural principle of VELES.

---

# Technology Stack

Current core technologies include:

- Python
- Flask
- PostgreSQL
- SQLAlchemy
- Ollama
- PyTorch
- Piper TTS
- Linux
- Git

Additional technologies may be introduced as individual modules evolve.

---

# Development Principles

VELES follows several core principles.

## Generic

VELES should work in different environments without hardcoded infrastructure.

## Modular

Operational domains remain separated into modules while sharing common operational concepts.

## Observable

System state and operations should be visible.

## Verifiable

Operations should be verified rather than assuming success.

## Controlled

Automation and AI actions must respect operational boundaries.

## Incremental

Stable functionality should be preserved while new functionality is introduced.

## Reusable

Existing working architecture, UI patterns and backend services should be reused rather than creating unnecessary parallel implementations.

## No Hardcoding

Environment-specific values must never be hardcoded into the project.

This includes:

- IP addresses
- Hostnames
- Credentials
- Network interfaces
- User-specific infrastructure

## Backend Stability

Existing stable backend architecture should not be changed without a clear reason.

## CLI and Web

CLI and Web interfaces should remain aligned with the same underlying services and operational models.

---

# Operational Safety

VELES is designed around controlled operations.

The intended lifecycle is:

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

The long-term objective is to support increasingly autonomous operations while keeping execution observable, controlled and verifiable.

---

# Development Workflow

VELES development follows an incremental approach.

Before major changes:

1. Check the current Git state.
2. Understand the existing architecture.
3. Preserve working modules.
4. Change only the required components.
5. Test the affected functionality.
6. Restart the systemd service.
7. Verify service status and logs.
8. Commit only the intended changes.

VELES runs as a systemd service.

The application should be managed through systemctl and not by manually starting the Flask application in production.

Example:

sudo systemctl restart veles
sudo systemctl status veles --no-pager
sudo journalctl -u veles -n 30 --no-pager

---

# Project Structure

The project is organized around modular operational services.

Core areas include:

veles/
├── modules/
│   ├── infrastructure/
│   ├── monitoring/
│   ├── network/
│   ├── delivery/
│   └── ...
│
├── web/
│   ├── templates/
│   ├── static/
│   └── app.py
│
└── ...

Modules should remain logically separated while sharing common infrastructure and service patterns.

---

# Operational Model

VELES is designed to gradually evolve from observation toward controlled autonomous operations.

The operational model is:

OBSERVE
   ↓
UNDERSTAND
   ↓
PLAN
   ↓
APPROVE
   ↓
EXECUTE
   ↓
VERIFY
   ↓
REPORT

This model is intended to become the foundation for future AI-assisted and automated operations.

---

# Roadmap

## Phase 1 — Operations Foundation

- Web Operations Center
- Dashboard
- AI Chat foundation
- Memory foundation
- Infrastructure Registry
- PostgreSQL backend
- Discovery
- Resource Identity
- Resource Verification
- Monitoring foundation
- Local Security foundation

## Phase 2 — Operational Intelligence

- Deeper AI operational context
- Infrastructure reasoning
- Incident analysis
- Improved planning
- AI-assisted remediation
- Advanced monitoring
- Persistent monitoring history
- Advanced security analysis

## Phase 3 — Operations

- Alerting
- Delivery workflows
- Automation
- Network operations
- Security operations
- Cloud operations
- Platform operations
- Data operations
- Testing operations

## Phase 4 — Autonomous Operations

- Policy-driven execution
- Approval workflows
- Automated remediation
- Continuous verification
- Multi-resource reasoning
- Incident response automation

## Phase 5 — Voice Operations

- Piper integration
- Voice pipeline
- Serbian TTS
- Voice interface
- Voice-controlled operations

---

# Current Development Direction

VELES is currently focused on building a stable operational foundation before moving into deeper automation and autonomous operations.

The current priority is:

Infrastructure
      ↓
Discovery
      ↓
Monitoring
      ↓
Security
      ↓
Network / Delivery
      ↓
Automation
      ↓
Cloud / Platform / Data / Testing
      ↓
Autonomous Operations

The development strategy is incremental:

Build a reliable operational foundation first.

Then connect intelligence, automation and autonomous capabilities to it.

---

# Project Status

VELES is an actively developed project.

Current focus:

AI
+
Infrastructure
+
Discovery
+
Monitoring
+
Security
+
Operations

Long-term direction:

SEE
  ↓
UNDERSTAND
  ↓
PLAN
  ↓
ACT
  ↓
VERIFY
  ↓
REPORT

VELES is being built as an AI Operations Center for real infrastructure operations.