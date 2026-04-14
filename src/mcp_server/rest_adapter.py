"""REST adapter — calls the backend API or falls back to mock data when REST_API_BASE_URL is unset."""

from typing import Optional

import httpx

from src.config import config
from src.mcp_server.mock_data import MOCK_CHARGEMENTS, MOCK_CLIENTS


class RestAdapter:
    def __init__(self) -> None:
        base = config.rest_api_base_url
        self.base_url = base.rstrip("/") if base else None
        self.api_key = config.rest_api_key
        self.use_mock = not bool(self.base_url)

    # ------------------------------------------------------------------ clients

    async def search_client(self, name: str, limit: int = 10) -> dict:
        if self.use_mock:
            results = [c for c in MOCK_CLIENTS if name.lower() in c["nom"].lower()]
            results = results[:limit]
            return {"clients": results, "total": len(results)}

        async with httpx.AsyncClient() as http:
            resp = await http.get(
                f"{self.base_url}/clients",
                params={"nom": name, "limit": limit},
                headers=self._headers(),
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_client(self, client_id: str) -> dict:
        if self.use_mock:
            for client in MOCK_CLIENTS:
                if client["id"] == client_id:
                    return client
            return {"error": f"Client '{client_id}' non trouvé"}

        async with httpx.AsyncClient() as http:
            resp = await http.get(
                f"{self.base_url}/clients/{client_id}",
                headers=self._headers(),
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()

    # --------------------------------------------------------------- chargements

    async def get_chargement(self, chargement_id: str) -> dict:
        if self.use_mock:
            for chargement in MOCK_CHARGEMENTS:
                if chargement["id"] == chargement_id:
                    return chargement
            return {"error": f"Chargement '{chargement_id}' non trouvé"}

        async with httpx.AsyncClient() as http:
            resp = await http.get(
                f"{self.base_url}/chargements/{chargement_id}",
                headers=self._headers(),
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()

    async def search_chargements(
        self,
        client_id: Optional[str] = None,
        statut: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 10,
    ) -> dict:
        if self.use_mock:
            results = list(MOCK_CHARGEMENTS)
            if client_id:
                results = [c for c in results if c["client_id"] == client_id]
            if statut:
                results = [c for c in results if c["statut"] == statut]
            if date_from:
                results = [c for c in results if c["date_enlevement"] >= date_from]
            if date_to:
                results = [c for c in results if c["date_enlevement"] <= date_to]
            results = results[:limit]
            return {"chargements": results, "total": len(results)}

        async with httpx.AsyncClient() as http:
            params: dict = {"limit": limit}
            if client_id:
                params["client_id"] = client_id
            if statut:
                params["statut"] = statut
            if date_from:
                params["date_from"] = date_from
            if date_to:
                params["date_to"] = date_to

            resp = await http.get(
                f"{self.base_url}/chargements",
                params=params,
                headers=self._headers(),
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()

    # ---------------------------------------------------------------------- helpers

    def _headers(self) -> dict:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
