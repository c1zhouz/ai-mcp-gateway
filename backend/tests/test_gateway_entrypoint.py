import json
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch

import httpx

from backend.app.main import app
from backend.app.models import database


async def _insert_gateway_fixture(key_value: str = "gw-test-key"):
    db = await database.get_db()
    await db.execute(
        "INSERT INTO services (id, name, address, status, created_at) VALUES (?, ?, ?, ?, ?)",
        ["svc-1", "Mall", "http://127.0.0.1:5001", "online", datetime.now().isoformat()],
    )
    await db.execute(
        "INSERT INTO tools (id, service_id, name, description, parameters_schema, enabled) VALUES (?, ?, ?, ?, ?, ?)",
        ["tool-1", "svc-1", "list_goods", "List goods", json.dumps({"type": "object"}), 1],
    )
    await db.execute(
        "INSERT INTO route_rules (id, path_pattern, target_service_id, priority, enabled) VALUES (?, ?, ?, ?, ?)",
        ["route-1", "/mall/*", "svc-1", 10, 1],
    )
    await db.execute(
        "INSERT INTO api_keys (id, name, key_value, permissions, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        ["key-1", "test", key_value, json.dumps(["read", "write"]), "active", datetime.now().isoformat()],
    )
    await db.commit()
    await db.close()


class GatewayEntrypointTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        database.DB_PATH = f"{self.tmp.name}/gateway.db"
        await database.init_db()
        self.transport = httpx.ASGITransport(app=app)

    async def asyncTearDown(self):
        await self.transport.aclose()
        self.tmp.cleanup()

    async def test_gateway_rejects_missing_bearer_token(self):
        await _insert_gateway_fixture()
        async with httpx.AsyncClient(transport=self.transport, base_url="http://test") as client:
            response = await client.post(
                "/gateway/mall/tools",
                json={"jsonrpc": "2.0", "id": "1", "method": "tools/list"},
            )

        self.assertEqual(response.status_code, 401)

    async def test_gateway_routes_authorized_tool_call_to_target_service(self):
        await _insert_gateway_fixture()

        async def fake_execute_tool(service_url, tool_name, arguments):
            return {
                "status": "success",
                "content": [{"type": "text", "text": f"{service_url}:{tool_name}:{arguments['goods_id']}"}],
            }

        with patch("backend.app.api.gateway.execute_tool", fake_execute_tool):
            async with httpx.AsyncClient(transport=self.transport, base_url="http://test") as client:
                response = await client.post(
                    "/gateway/mall/tools",
                    headers={"Authorization": "Bearer gw-test-key"},
                    json={
                        "jsonrpc": "2.0",
                        "id": "call-1",
                        "method": "tools/call",
                        "params": {"name": "list_goods", "arguments": {"goods_id": "SKU_1"}},
                    },
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "jsonrpc": "2.0",
                "id": "call-1",
                "result": {
                    "content": [{"type": "text", "text": "http://127.0.0.1:5001:list_goods:SKU_1"}]
                },
            },
        )

    async def test_gateway_returns_404_when_no_route_matches(self):
        await _insert_gateway_fixture()
        async with httpx.AsyncClient(transport=self.transport, base_url="http://test") as client:
            response = await client.post(
                "/gateway/unknown/tools",
                headers={"Authorization": "Bearer gw-test-key"},
                json={"jsonrpc": "2.0", "id": "1", "method": "tools/list"},
            )

        self.assertEqual(response.status_code, 404)
