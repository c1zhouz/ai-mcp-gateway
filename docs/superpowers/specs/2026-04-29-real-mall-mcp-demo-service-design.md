# Real Mall MCP Demo Service Design

## Goal

Turn `services/real_mall_mcp` into a focused group-buying mall MCP Server for internship demos. The service should expose real business tools around group-buy activities, teams, discounts, SKUs, and orders instead of a broad set of mostly mocked ecommerce tools.

## Data Strategy

The service keeps the existing `DATABASE_URL` behavior so it can connect to the user's original `group_buy_market` MySQL database. Runtime tools must use only that configured primary database. They must not retry against a local demo database when MySQL is unavailable or when the query returns no rows.

## Tool Set

The MCP Server exposes these tools:

- `list_active_group_buy_activities`
- `get_activity_detail`
- `get_team_progress`
- `analyze_activity_sales`
- `get_sku_sales_ranking`
- `get_discount_effectiveness`
- `find_unfinished_teams`
- `get_user_group_buy_history`

Each tool returns structured dictionaries/lists that are easy for an LLM to summarize. Read-only analysis tools are preferred. The service does not expose simulated logistics, suppliers, forecasts, or code-writing/deployment features.

## Boundaries

Gateway code remains responsible for service registration, tool discovery, routing, API key checks, and call logs. Group-buying business logic lives only inside the MCP Server. The demo service does not modify the production MySQL database; seed data is written only to the local SQLite demo database.

## Verification

Unit tests use an isolated temporary SQLite database as a test fixture only. Runtime configuration and documentation use the real `group_buy_market` database. Full project verification should include service tests, backend tests, frontend lint, and frontend build.
