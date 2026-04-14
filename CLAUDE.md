# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered operations platform for a logistics transport company. The system lets AI agents understand natural-language user requests, discover and call enterprise tools (via MCP), retrieve data through connected APIs, and return concise reasoned answers. It also executes operational actions (create notes, update statuses, assign tasks) when the user has permission.

Full technical specification is in [SPEC.md](SPEC.md).

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run a single test file
pytest path/to/test_file.py

# Run a single test
pytest path/to/test_file.py::test_name
```

## Architecture

```
[ Client / UI / Chat Frontend ]
             |
[ API Layer / Session Gateway ]
             |
[ Agent Runtime / Orchestrator ]
     |         |          |         |
[MCP Tool] [REST Adapter] [Doc Retriever] [Policy/Guardrail]
 Servers      Layer           Layer           Engine
     |            |               |
Existing     Existing APIs   Functional Docs / KB
Systems      through gateway
```

**Core components to implement:**

- **Agent Runtime / Orchestrator** — Coordinates intent resolution, tool selection, multi-agent delegation, and response synthesis. Preserves short-term session memory (resolved entities, prior tool results, conversation history).
- **MCP Tool Servers** — Dynamic tool discovery: each tool exposes name, description, input schema, auth requirements, and action type (`read` / `write` / `destructive`).
- **REST Adapter Layer** — Wraps existing enterprise APIs (TMS/ERP/CRM) behind a uniform interface; validates inputs before execution.
- **Document Retriever Layer** — Queries SOPs, transport procedures, customer-specific operating rules, and business glossaries as knowledge sources.
- **Policy/Guardrail Engine** — Enforces RBAC/ABAC authorization, validates action permissions, and protects against prompt injection from external tool descriptions and documents.

**Multi-agent roles (optional specialization):** Orchestrator, Tool Router, Data Retrieval, Document Retrieval, Response Composer, Action Guard.

## Implementation Stack

- **Language:** Python with OpenAI SDK
- **Web framework:** FastAPI + Uvicorn
- **Data validation:** Pydantic
- **Testing:** pytest + pytest-asyncio
- **Deployment:** AWS AgentCore

## Key Constraints

**Security (non-negotiable):**
- Every tool action and material data read must be audit-logged: timestamp, user ID, session ID, tools selected, inputs, outputs, final answer, confidence metadata.
- Authorization checks before any write/destructive action; high-risk actions require explicit confirmation.
- Prompt injection protection for external tool descriptions and retrieved documents.

**Reliability:**
- Parallel tool calls where safe (concurrent sessions, multi-tool queries).
- Graceful degradation on partial tool outages, timeouts, malformed API responses, or missing tools.
- Retryable vs. non-retryable error distinction.

**Maintainability:**
- New tools, prompts, document sources, and business rules must be configurable without code changes.

## Domain Context

Core logistics entities: shipments, customers, carriers, routes, delays, transport instructions, delivery notes, incidents, loads, ETAs.

Latency targets: simple read <5s, multi-tool read <12s, action execution <15s, complex investigations → streaming.
