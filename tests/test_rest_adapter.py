"""Tests for the REST adapter using mock data (no REST_API_BASE_URL configured)."""

import pytest

from src.mcp_server.rest_adapter import RestAdapter


@pytest.fixture
def adapter() -> RestAdapter:
    a = RestAdapter()
    assert a.use_mock, "Tests require mock mode — unset REST_API_BASE_URL before running"
    return a


# ------------------------------------------------------------------ clients


async def test_search_client_found(adapter):
    result = await adapter.search_client(name="Dupont")
    assert result["total"] >= 1
    assert any("Dupont" in c["nom"] for c in result["clients"])


async def test_search_client_partial_match(adapter):
    result = await adapter.search_client(name="transport")
    assert result["total"] >= 1


async def test_search_client_no_match(adapter):
    result = await adapter.search_client(name="zzz_inexistant_zzz")
    assert result["total"] == 0
    assert result["clients"] == []


async def test_search_client_limit(adapter):
    result = await adapter.search_client(name="", limit=2)
    assert len(result["clients"]) <= 2


async def test_get_client_exists(adapter):
    result = await adapter.get_client("CLT-001")
    assert result["id"] == "CLT-001"
    assert result["nom"] == "Dupont Transports"
    assert "contact" in result
    assert "adresse" in result


async def test_get_client_not_found(adapter):
    result = await adapter.get_client("CLT-999")
    assert "error" in result


# ---------------------------------------------------------------- chargements


async def test_get_chargement_exists(adapter):
    result = await adapter.get_chargement("CHG-2026-00891")
    assert result["id"] == "CHG-2026-00891"
    assert result["client_id"] == "CLT-001"
    assert "statut" in result
    assert "origine" in result
    assert "destination" in result


async def test_get_chargement_not_found(adapter):
    result = await adapter.get_chargement("CHG-9999-00000")
    assert "error" in result


async def test_search_chargements_no_filter(adapter):
    result = await adapter.search_chargements()
    assert "chargements" in result
    assert result["total"] >= 1


async def test_search_chargements_by_client(adapter):
    result = await adapter.search_chargements(client_id="CLT-001")
    assert result["total"] >= 1
    for c in result["chargements"]:
        assert c["client_id"] == "CLT-001"


async def test_search_chargements_by_statut(adapter):
    result = await adapter.search_chargements(statut="en_cours")
    assert result["total"] >= 1
    for c in result["chargements"]:
        assert c["statut"] == "en_cours"


async def test_search_chargements_by_date_range(adapter):
    result = await adapter.search_chargements(date_from="2026-04-12", date_to="2026-04-14")
    for c in result["chargements"]:
        assert "2026-04-12" <= c["date_enlevement"] <= "2026-04-14"


async def test_search_chargements_combined_filters(adapter):
    result = await adapter.search_chargements(client_id="CLT-001", statut="en_cours")
    for c in result["chargements"]:
        assert c["client_id"] == "CLT-001"
        assert c["statut"] == "en_cours"
