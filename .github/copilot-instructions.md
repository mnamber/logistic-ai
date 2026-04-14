# Project Guidelines

## Architecture

This is an AI-powered operations platform for a logistics transport company. The system integrates with MCP servers, REST APIs, and functional documents to handle natural-language requests, discover tools, retrieve data, and execute actions.

Key components:
- Agent Runtime / Orchestrator
- MCP Tool Servers
- REST Adapter Layer
- Document Retriever Layer
- Policy/Guardrail Engine

See [SPEC.md](SPEC.md) for detailed technical specification.

## Build and Test

- Install dependencies: `pip install -r requirements.txt` (create if not present)
- Run tests: `pytest` (assuming pytest for testing)

## Conventions

- Use Python for implementation with OpenAI SDK.
- Ensure security: authenticated access, role-based authorization, audit logging for all actions.
- Handle errors gracefully, log tool calls, inputs, outputs.
- Domain focus: Logistics operations including shipments, customers, carriers, routes, delays.
- Deployment target: AWS AgentCore environment.