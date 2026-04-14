"""Logistics AI agent — connects to the MCP server via SSE, runs an OpenAI tool-calling loop."""

import json
import logging

from mcp import ClientSession
from mcp.client.sse import sse_client
from openai import AsyncOpenAI

from src.agent.audit import AuditLogger
from src.agent.session import SessionMemory
from src.config import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
Tu es un assistant IA pour une entreprise de transport logistique.
Tu aides les opérateurs, les chargés de clientèle et les dispatcheurs à trouver \
des informations sur les clients et les chargements.

Règles :
- Utilise les outils disponibles pour récupérer des informations précises et à jour.
- Réponds toujours dans la même langue que l'utilisateur.
- Sois concis et précis dans tes réponses.
- Si un nom de client est ambigu, effectue d'abord une recherche pour lever l'ambiguïté.
- Ne fabrique jamais de données : base-toi uniquement sur les résultats des outils.
"""


class LogisticsAgent:
    def __init__(self, session_id: str = "default") -> None:
        self.session_id = session_id
        self._openai = AsyncOpenAI(api_key=config.openai_api_key)
        self._memory = SessionMemory(session_id)
        self._audit = AuditLogger()

    async def chat(self, user_message: str) -> str:
        """Process a natural-language message and return a grounded response."""
        self._memory.add_message("user", user_message)
        try:
            response = await self._run_with_mcp()
        except Exception as exc:
            logger.error("Agent error for session %s: %s", self.session_id, exc)
            response = f"Une erreur est survenue lors du traitement de votre demande : {exc}"
        self._memory.add_message("assistant", response)
        return response

    # ------------------------------------------------------------------ internals

    async def _run_with_mcp(self) -> str:
        async with sse_client(url=config.mcp_server_url) as (read, write):
            async with ClientSession(read, write) as mcp_session:
                await mcp_session.initialize()
                tools_result = await mcp_session.list_tools()
                tools = self._to_openai_tools(tools_result.tools)
                messages: list[dict] = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *self._memory.get_history(),
                ]
                return await self._completion_loop(mcp_session, messages, tools)

    async def _completion_loop(
        self,
        mcp_session: ClientSession,
        messages: list,
        tools: list,
    ) -> str:
        while True:
            kwargs: dict = {"model": config.openai_model, "messages": messages}
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            completion = await self._openai.chat.completions.create(**kwargs)
            msg = completion.choices[0].message

            if not msg.tool_calls:
                return msg.content or ""

            # Append assistant message with tool_calls before adding tool results
            messages.append(msg)

            for tool_call in msg.tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                result_text = await self._call_mcp_tool(mcp_session, name, args)

                self._audit.log_tool_call(
                    session_id=self.session_id,
                    tool_name=name,
                    inputs=args,
                    output_summary=result_text,
                )

                messages.append(
                    {"role": "tool", "tool_call_id": tool_call.id, "content": result_text}
                )

    async def _call_mcp_tool(
        self, mcp_session: ClientSession, name: str, args: dict
    ) -> str:
        try:
            result = await mcp_session.call_tool(name, args)
            if result.isError:
                return json.dumps({"error": f"Tool error: {result.content}"}, ensure_ascii=False)
            if result.content:
                return result.content[0].text
            return json.dumps({"result": None})
        except Exception as exc:
            logger.error("Tool call failed [%s]: %s", name, exc)
            return json.dumps({"error": str(exc)}, ensure_ascii=False)

    @staticmethod
    def _to_openai_tools(mcp_tools) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema,
                },
            }
            for tool in mcp_tools
        ]
