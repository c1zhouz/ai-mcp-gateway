import json
import tempfile
import unittest
from unittest.mock import patch

import httpx

from backend.app.main import app
from backend.app.models import database


class ChatSessionTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        database.DB_PATH = f"{self.tmp.name}/gateway.db"
        await database.init_db()
        self.transport = httpx.ASGITransport(app=app)
        self.calls = []

    async def asyncTearDown(self):
        await self.transport.aclose()
        self.tmp.cleanup()

    async def _send(self, message, session_id=None):
        async def fake_run_agent(**kwargs):
            self.calls.append(kwargs)
            yield {"event": "message", "data": json.dumps({"content": f"reply:{kwargs['message']}"})}
            yield {"event": "done", "data": json.dumps({"usage": {"prompt_tokens": 1, "completion_tokens": 1}})}

        payload = {"message": message, "llm_api_key": "sk-test", "model": "test-model"}
        if session_id:
            payload["session_id"] = session_id

        with patch("backend.app.api.chat.run_agent", fake_run_agent):
            async with httpx.AsyncClient(transport=self.transport, base_url="http://test") as client:
                response = await client.post("/api/chat/send", json=payload)
                await response.aread()
                return response

    async def test_send_message_creates_session_and_persists_messages(self):
        response = await self._send("hello")

        self.assertEqual(response.status_code, 200)
        text = response.text
        self.assertIn("event: session", text)

        db = await database.get_db()
        sessions = await db.execute("SELECT * FROM chat_sessions")
        session_rows = [dict(r) async for r in sessions]
        messages = await db.execute("SELECT role, content FROM chat_messages ORDER BY timestamp")
        message_rows = [dict(r) async for r in messages]
        await db.close()

        self.assertEqual(len(session_rows), 1)
        self.assertEqual(session_rows[0]["message_count"], 2)
        self.assertEqual(message_rows, [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "reply:hello"},
        ])

    async def test_existing_session_history_is_passed_to_agent(self):
        await self._send("hello")
        db = await database.get_db()
        row = await db.execute("SELECT id FROM chat_sessions")
        session = await row.fetchone()
        await db.close()

        await self._send("again", session_id=session["id"])

        self.assertEqual(self.calls[-1]["history"], [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "reply:hello"},
        ])
