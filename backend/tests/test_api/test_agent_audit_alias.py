"""Agent audit list API — versioned path and non-versioned /api/admin alias."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_agent_audit_v1_and_alias_same_behavior(
    client: AsyncClient,
    admin_token: str,
) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    v1 = await client.get("/api/v1/admin/agent-audit", headers=headers)
    alias = await client.get("/api/admin/agent-audit", headers=headers)

    assert v1.status_code == 200
    assert alias.status_code == 200

    body_v1 = v1.json()["data"]
    body_alias = alias.json()["data"]
    assert body_v1.keys() == body_alias.keys()
    assert "items" in body_v1 and "total" in body_v1
    assert body_v1["total"] == body_alias["total"]
    assert body_v1["items"] == body_alias["items"]
