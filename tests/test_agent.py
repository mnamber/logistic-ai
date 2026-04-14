"""Unit tests for the agent — mocks both OpenAI and MCP so no network is required."""

import json

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agent.agent import LogisticsAgent


# ------------------------------------------------------------------ helpers


def _mcp_tool(name: str, description: str = "", schema: dict | None = None):
    tool = MagicMock()
    tool.name = name
    tool.description = description
    tool.inputSchema = schema or {"type": "object", "properties": {}}
    return tool


def _openai_response(content: str | None = None, tool_calls: list | None = None):
    msg = MagicMock()
    msg.content = content
    msg.tool_calls = tool_calls or []
    choice = MagicMock()
    choice.message = msg
    completion = MagicMock()
    completion.choices = [choice]
    return completion


def _mcp_result(data: dict):
    text_content = MagicMock()
    text_content.text = json.dumps(data, ensure_ascii=False)
    result = MagicMock()
    result.isError = False
    result.content = [text_content]
    return result


# ------------------------------------------------------------------ unit tests


def test_to_openai_tools_conversion():
    agent = LogisticsAgent(session_id="test")
    mcp_tools = [
        _mcp_tool("search_client", "Search client", {"type": "object", "properties": {"name": {"type": "string"}}}),
        _mcp_tool("get_chargement", "Get shipment", {"type": "object", "properties": {"chargement_id": {"type": "string"}}}),
    ]
    tools = agent._to_openai_tools(mcp_tools)
    assert len(tools) == 2
    assert tools[0]["type"] == "function"
    assert tools[0]["function"]["name"] == "search_client"
    assert tools[1]["function"]["name"] == "get_chargement"


async def test_call_mcp_tool_success():
    agent = LogisticsAgent(session_id="test")
    mock_mcp = AsyncMock()
    mock_mcp.call_tool.return_value = _mcp_result({"id": "CLT-001", "nom": "Dupont Transports"})

    result = await agent._call_mcp_tool(mock_mcp, "get_client", {"client_id": "CLT-001"})
    parsed = json.loads(result)
    assert parsed["id"] == "CLT-001"
    mock_mcp.call_tool.assert_called_once_with("get_client", {"client_id": "CLT-001"})


async def test_call_mcp_tool_error_flag():
    agent = LogisticsAgent(session_id="test")
    mock_mcp = AsyncMock()
    err_result = MagicMock()
    err_result.isError = True
    err_result.content = "Tool not found"
    mock_mcp.call_tool.return_value = err_result

    result = await agent._call_mcp_tool(mock_mcp, "unknown_tool", {})
    parsed = json.loads(result)
    assert "error" in parsed


async def test_completion_loop_direct_answer():
    """When OpenAI returns no tool calls, the loop exits immediately."""
    agent = LogisticsAgent(session_id="test")
    mock_mcp = AsyncMock()
    mock_create = AsyncMock(return_value=_openai_response(content="Voici le résultat."))

    with patch.object(agent._openai.chat.completions, "create", mock_create):
        result = await agent._completion_loop(
            mock_mcp,
            [{"role": "user", "content": "Cherche Dupont"}],
            [],
        )

    assert result == "Voici le résultat."
    mock_mcp.call_tool.assert_not_called()


async def test_completion_loop_single_tool_call():
    """Agent calls a tool once, receives its result, then produces a final answer."""
    agent = LogisticsAgent(session_id="test")

    tool_call = MagicMock()
    tool_call.id = "call_abc"
    tool_call.function.name = "search_client"
    tool_call.function.arguments = json.dumps({"name": "Dupont"})

    first_resp = _openai_response(tool_calls=[tool_call])
    second_resp = _openai_response(content="J'ai trouvé le client Dupont Transports (CLT-001).")

    mock_mcp = AsyncMock()
    mock_mcp.call_tool.return_value = _mcp_result(
        {"clients": [{"id": "CLT-001", "nom": "Dupont Transports"}], "total": 1}
    )

    call_count = 0

    async def mock_create(**kwargs):
        nonlocal call_count
        call_count += 1
        return first_resp if call_count == 1 else second_resp

    with patch.object(agent._openai.chat.completions, "create", side_effect=mock_create):
        result = await agent._completion_loop(
            mock_mcp,
            [{"role": "user", "content": "Cherche le client Dupont"}],
            [{"type": "function", "function": {"name": "search_client", "description": "", "parameters": {}}}],
        )

    assert "Dupont" in result
    mock_mcp.call_tool.assert_called_once_with("search_client", {"name": "Dupont"})


async def test_chat_stores_messages_in_memory():
    """chat() should store the user message and agent response in session memory."""
    agent = LogisticsAgent(session_id="mem-test")

    async def fake_run_with_mcp():
        return "Réponse simulée"

    with patch.object(agent, "_run_with_mcp", fake_run_with_mcp):
        await agent.chat("Bonjour")

    history = agent._memory.get_history()
    assert any(m["role"] == "user" and m["content"] == "Bonjour" for m in history)
    assert any(m["role"] == "assistant" and m["content"] == "Réponse simulée" for m in history)
