import aiosqlite
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "gateway.db")


async def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    db = await get_db()
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS services (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            description TEXT DEFAULT '',
            status TEXT DEFAULT 'offline',
            health_check_interval INTEGER DEFAULT 30,
            auto_reconnect INTEGER DEFAULT 1,
            tool_count INTEGER DEFAULT 0,
            last_heartbeat TEXT,
            created_at TEXT NOT NULL,
            source_file TEXT DEFAULT '',
            python_path TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS tools (
            id TEXT PRIMARY KEY,
            service_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            parameters_schema TEXT DEFAULT '{}',
            enabled INTEGER DEFAULT 1,
            call_count INTEGER DEFAULT 0,
            code TEXT DEFAULT '',
            FOREIGN KEY (service_id) REFERENCES services(id)
        );

        CREATE TABLE IF NOT EXISTS gateway_config (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT DEFAULT 'AI MCP Gateway',
            listen_address TEXT DEFAULT '0.0.0.0',
            port INTEGER DEFAULT 8777,
            timeout_ms INTEGER DEFAULT 30000,
            max_concurrency INTEGER DEFAULT 100,
            log_level TEXT DEFAULT 'INFO',
            log_retention_days INTEGER DEFAULT 7
        );

        CREATE TABLE IF NOT EXISTS api_keys (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            key_value TEXT NOT NULL,
            permissions TEXT DEFAULT '["read"]',
            expires_at TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS route_rules (
            id TEXT PRIMARY KEY,
            path_pattern TEXT NOT NULL,
            target_service_id TEXT NOT NULL,
            priority INTEGER DEFAULT 0,
            enabled INTEGER DEFAULT 1,
            FOREIGN KEY (target_service_id) REFERENCES services(id)
        );

        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY,
            title TEXT DEFAULT '',
            service_id TEXT,
            message_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS chat_messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT DEFAULT '',
            thinking TEXT,
            tool_calls TEXT DEFAULT '[]',
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
        );

        CREATE TABLE IF NOT EXISTS request_history (
            time_hour TEXT PRIMARY KEY, -- 格式: YYYY-MM-DD HH:00
            count INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0
        );

        INSERT OR IGNORE INTO gateway_config (id) VALUES (1);
    """)
    await db.commit()

    # Migrate existing databases: add new columns if they don't exist
    migrations = [
        ("tools", "code", "TEXT DEFAULT ''"),
        ("services", "source_file", "TEXT DEFAULT ''"),
        ("services", "python_path", "TEXT DEFAULT ''"),
    ]
    for table, col, col_def in migrations:
        try:
            await db.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}")
            await db.commit()
        except Exception:
            pass  # Column already exists

    await db.close()
