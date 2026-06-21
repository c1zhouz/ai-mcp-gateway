import tempfile
import unittest
from datetime import datetime

import httpx

from backend.app.main import app
from backend.app.models import database


class SafeToolDeployTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        database.DB_PATH = f"{self.tmp.name}/gateway.db"
        await database.init_db()
        self.transport = httpx.ASGITransport(app=app)

    async def asyncTearDown(self):
        await self.transport.aclose()
        self.tmp.cleanup()

    async def test_tool_deploy_endpoint_is_not_exposed(self):
        db = await database.get_db()
        await db.execute(
            "INSERT INTO services (id, name, address, status, created_at) VALUES (?, ?, ?, ?, ?)",
            ["svc-1", "Mall", "http://127.0.0.1:5001", "online", datetime.now().isoformat()],
        )
        await db.execute(
            "INSERT INTO tools (id, service_id, name, description, parameters_schema, enabled) VALUES (?, ?, ?, ?, ?, ?)",
            ["tool-1", "svc-1", "safe_tool", "Return a safe result", "{}", 1],
        )
        await db.commit()
        await db.close()

        async with httpx.AsyncClient(transport=self.transport, base_url="http://test") as client:
            response = await client.post("/api/tools/tool-1/deploy")

        self.assertEqual(response.status_code, 404)

    async def test_manual_tool_write_endpoints_are_not_exposed(self):
        async with httpx.AsyncClient(transport=self.transport, base_url="http://test") as client:
            create_response = await client.post("/api/tools", json={
                "service_id": "svc-1",
                "name": "unsafe_tool",
                "parameters_schema": {},
            })
            update_response = await client.put("/api/tools/tool-1", json={"description": "changed"})

        self.assertEqual(create_response.status_code, 405)
        self.assertEqual(update_response.status_code, 405)
