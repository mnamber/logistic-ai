"""FastAPI application — HTTP interface for the logistics agent.

Run:
    uvicorn src.api.main:app --reload --port 8000
"""

from fastapi import FastAPI

from src.agent.agent import LogisticsAgent
from src.api.models import ChatRequest, ChatResponse

app = FastAPI(
    title="Logistics AI Agent",
    description="AI agent for logistics transport operations — client and chargement lookup.",
    version="0.1.0",
)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Send a natural-language message; receive a grounded response from the agent."""
    agent = LogisticsAgent(session_id=request.session_id)
    response = await agent.chat(request.message)
    return ChatResponse(response=response, session_id=request.session_id)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
