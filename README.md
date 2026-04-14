# Logistic AI Agent

An AI-powered operations platform for a logistics transport company, built by **AGITEX**.

The system lets AI agents understand natural-language requests from operations teams, discover and call enterprise tools via the **Model Context Protocol (MCP)**, retrieve data through connected REST APIs, and return concise, grounded answers.

---

## Features

- **Natural language queries** — ask questions about clients and chargements in plain French or English
- **MCP tool layer** — agent dynamically discovers and calls tools via FastMCP over SSE
- **REST adapter** — pluggable backend: point at your real TMS/ERP API or run with built-in mock data
- **Conversation memory** — session context preserved across follow-up questions
- **Audit logging** — every tool call logged with timestamp, inputs, and output summary
- **Gradio UI** — chat interface with markdown/table rendering and conversation history
- **REST API** — FastAPI `POST /chat` endpoint for programmatic access

---

## Architecture

```
[ Gradio UI / FastAPI ]
          │
[ Agent Runtime (OpenAI SDK) ]
          │  tool-calling loop
[ MCP Server (FastMCP / SSE) ]
          │
[ REST Adapter ]
          │
[ Backend REST API ]   ← or mock data for development
```

**Key components:**

| Module | Role |
|---|---|
| `src/mcp_server/server.py` | FastMCP server exposing 4 logistics tools over SSE |
| `src/mcp_server/rest_adapter.py` | HTTP client wrapping the backend API (with mock fallback) |
| `src/mcp_server/mock_data.py` | Sample clients and chargements for development |
| `src/agent/agent.py` | OpenAI tool-calling loop — connects to MCP, synthesises responses |
| `src/agent/session.py` | In-process session memory (conversation history per session) |
| `src/agent/audit.py` | Structured audit logger for all tool calls |
| `src/api/main.py` | FastAPI app with `POST /chat` endpoint |
| `src/ui/gradio_app.py` | Gradio chat UI |

---

## MCP Tools

| Tool | Description |
|---|---|
| `search_client(name, limit)` | Search clients by name |
| `get_client(client_id)` | Get full client details by ID |
| `get_chargement(chargement_id)` | Get a shipment/load by ID |
| `search_chargements(client_id, statut, date_from, date_to, limit)` | Filter shipments by client, status, or date range |

**Statuts:** `planifie` · `en_cours` · `livre` · `en_retard` · `annule`

---

## Quick Start

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY
```

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
MCP_SERVER_URL=http://localhost:8001/sse

# Leave empty to use built-in mock data
REST_API_BASE_URL=
REST_API_KEY=
```

### 3. Start the MCP server

```bash
python -m src.mcp_server.server
# Listening on http://0.0.0.0:8001/sse
```

### 4. Start the UI

```bash
# Option A — Gradio (recommended)
python -m src.ui.gradio_app
# Open http://localhost:7860

# Option B — REST API only
uvicorn src.api.main:app --reload --port 8000
# POST http://localhost:8000/chat
```

---

## Usage Examples

**Gradio UI** — type any of these into the chat:

```
Cherche le client Dupont
Donne-moi les chargements en cours pour CLT-001
Quel est le statut du chargement CHG-2026-00893 ?
Y a-t-il des chargements en retard ?
```

**REST API:**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Cherche le client Dupont", "session_id": "session-1"}'
```

```json
{
  "response": "J'ai trouvé le client **Dupont Transports** (CLT-001)...",
  "session_id": "session-1"
}
```

---

## Connecting a Real Backend

Set `REST_API_BASE_URL` in `.env` to your backend base URL. The adapter expects:

| Endpoint | Description |
|---|---|
| `GET /clients?nom=&limit=` | Search clients |
| `GET /clients/{id}` | Get client by ID |
| `GET /chargements/{id}` | Get chargement by ID |
| `GET /chargements?client_id=&statut=&date_from=&date_to=&limit=` | Search chargements |

---

## Running Tests

```bash
pytest

# Single file
pytest tests/test_rest_adapter.py
pytest tests/test_agent.py
```

Tests run entirely with mock data — no network or API key required.

---

## Tech Stack

- **Python 3.12+**
- [OpenAI SDK](https://github.com/openai/openai-python) — agent & tool-calling
- [FastMCP](https://github.com/jlowin/fastmcp) — MCP server
- [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) — REST API
- [Gradio](https://www.gradio.app/) — chat UI
- [Pydantic](https://docs.pydantic.dev/) — data validation
- [pytest](https://pytest.org/) + [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) — testing
- **AWS AgentCore** — deployment target

---

## Project Structure

```
src/
├── config.py
├── mcp_server/
│   ├── server.py          # FastMCP server (SSE, port 8001)
│   ├── rest_adapter.py    # REST client + mock fallback
│   └── mock_data.py       # Development data
├── agent/
│   ├── agent.py           # Orchestrator (OpenAI + MCP loop)
│   ├── session.py         # Conversation memory
│   └── audit.py           # Audit logger
├── api/
│   └── main.py            # FastAPI app
└── ui/
    └── gradio_app.py      # Gradio chat interface
tests/
├── test_rest_adapter.py
└── test_agent.py
```

---

Built with ❤️ by [AGITEX](https://github.com/mnamber)
