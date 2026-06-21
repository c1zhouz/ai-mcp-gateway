import json
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch

import httpx

from backend.app.main import app
from backend.app.models import database


class ServiceHealthCheckTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        database.DB_PATH = f"{self.tmp.name}/gateway.db"
        await database.init_db()
        self.transport = httpx.ASGITransport(app=app)

    async def asyncTearDown(self):
        await self.transport.aclose()
        self.tmp.cleanup()

    async def test_health_check_marks_service_offline_when_mcp_connection_fails(self):
        db = await database.get_db()
        await db.execute(
            "INSERT INTO services (id, name, address, status, created_at) VALUES (?, ?, ?, ?, ?)",
            ["svc-1", "Mall", "http://127.0.0.1:5999", "online", datetime.now().isoformat()],
        )
        await db.commit()
        await db.close()

        async def fake_health(_address):
            return {"ok": False, "error": "connection refused"}

        with patch("backend.app.api.services.check_service_health", fake_health):
            async with httpx.AsyncClient(transport=self.transport, base_url="http://test") as client:
                response = await client.post("/api/services/svc-1/health-check")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "connection refused")

        db = await database.get_db()
        row = await db.execute("SELECT status FROM services WHERE id=?", ["svc-1"])
        service = await row.fetchone()
        await db.close()
        self.assertEqual(service["status"], "offline")

    async def test_health_check_marks_service_online_and_syncs_tool_count(self):
        db = await database.get_db()
        await db.execute(
            "INSERT INTO services (id, name, address, status, created_at) VALUES (?, ?, ?, ?, ?)",
            ["svc-1", "Mall", "http://127.0.0.1:5001", "offline", datetime.now().isoformat()],
        )
        await db.commit()
        await db.close()

        async def fake_health(_address):
            return {
                "ok": True,
                "tools": [
                    {"name": "list_goods", "description": "List goods", "inputSchema": {"type": "object"}}
                ],
            }

        with patch("backend.app.api.services.check_service_health", fake_health):
            async with httpx.AsyncClient(transport=self.transport, base_url="http://test") as client:
                response = await client.post("/api/services/svc-1/health-check")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "online")

        db = await database.get_db()
        row = await db.execute("SELECT status, tool_count FROM services WHERE id=?", ["svc-1"])
        service = await row.fetchone()
        tools = await db.execute("SELECT name, parameters_schema FROM tools WHERE service_id=?", ["svc-1"])
        tool_rows = [dict(r) async for r in tools]
        await db.close()
        self.assertEqual(service["status"], "online")
        self.assertEqual(service["tool_count"], 1)
        self.assertEqual(tool_rows[0]["name"], "list_goods")
        self.assertEqual(json.loads(tool_rows[0]["parameters_schema"]), {"type": "object"})
