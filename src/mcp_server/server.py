"""FastMCP server — exposes logistics tools over SSE transport.

Run:
    python -m src.mcp_server.server
Then connects on http://localhost:8001/sse
"""

from typing import Optional

from fastmcp import FastMCP

from src.mcp_server.rest_adapter import RestAdapter

mcp = FastMCP(
    name="logistics-mcp",
    instructions=(
        "MCP server for a logistics transport company. "
        "Provides tools to search and retrieve clients and chargements (shipments/loads). "
        "Statuts possibles : planifie | en_cours | livre | en_retard | annule."
    ),
)

_adapter = RestAdapter()


@mcp.tool()
async def search_client(name: str, limit: int = 10) -> dict:
    """
    Search for a client (customer) by name.
    Returns a list of matching clients with id, nom, type, and statut.
    Use the returned id with get_client to retrieve full details.
    """
    return await _adapter.search_client(name=name, limit=limit)


@mcp.tool()
async def get_client(client_id: str) -> dict:
    """
    Retrieve full details of a client by their ID (e.g. CLT-001).
    Returns contact info, address, SIRET, and type.
    """
    return await _adapter.get_client(client_id=client_id)


@mcp.tool()
async def get_chargement(chargement_id: str) -> dict:
    """
    Retrieve full details of a chargement (shipment/load) by its ID (e.g. CHG-2026-00891).
    Returns origin, destination, statut, dates, carrier, driver, goods, and incident history.
    """
    return await _adapter.get_chargement(chargement_id=chargement_id)


@mcp.tool()
async def search_chargements(
    client_id: Optional[str] = None,
    statut: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 10,
) -> dict:
    """
    Search for chargements (shipments/loads) with optional filters.
    - client_id: filter by client ID (e.g. CLT-001)
    - statut: planifie | en_cours | livre | en_retard | annule
    - date_from: earliest pickup date YYYY-MM-DD
    - date_to: latest pickup date YYYY-MM-DD
    - limit: max results (default 10)
    """
    return await _adapter.search_chargements(
        client_id=client_id,
        statut=statut,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8001)
