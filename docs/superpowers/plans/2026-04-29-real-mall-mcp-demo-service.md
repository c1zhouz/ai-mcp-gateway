# Real Mall MCP Demo Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild `real-mall-mcp` as a stable group-buying mall MCP demo service.

**Architecture:** Keep the FastMCP server entrypoint in `main.py` and expand SQLAlchemy models for the group-buying schema. Runtime tools query only the configured `DATABASE_URL`; tests may use a temporary SQLite fixture.

**Tech Stack:** Python 3.11, FastMCP, SQLAlchemy async ORM, MySQL via aiomysql, SQLite via aiosqlite, unittest.

---

### Task 1: Lock Tool Behavior With Tests

**Files:**
- Create: `services/real_mall_mcp/tests/test_demo_tools.py`
- Modify after red: `services/real_mall_mcp/main.py`

- [ ] Write tests that seed a temporary SQLite demo database and assert `list_active_group_buy_activities`, `get_activity_detail`, `analyze_activity_sales`, `get_sku_sales_ranking`, `find_unfinished_teams`, and `get_user_group_buy_history` return group-buy business data.
- [ ] Run `DATABASE_URL=sqlite+aiosqlite:////tmp/real_mall_test.db ./venv/bin/python -m unittest discover tests -v` from `services/real_mall_mcp` and confirm the tests fail before implementation.

### Task 2: Expand Models And Seed Data

**Files:**
- Modify: `services/real_mall_mcp/models.py`
- Modify: `services/real_mall_mcp/.env.example`
- Modify: `services/real_mall_mcp/requirements.txt`

- [ ] Add SQLAlchemy models for `sku`, `group_buy_activity`, `group_buy_discount`, `group_buy_order`, `group_buy_order_list`, `sc_sku_activity`, and `crowd_tags`.
- [ ] Add deterministic test fixtures for activities, discounts, SKUs, teams, and orders.
- [ ] Add `aiomysql` to service requirements because the checked-in `.env` uses MySQL.

### Task 3: Replace Mock Tools With Group-Buy Tools

**Files:**
- Modify: `services/real_mall_mcp/main.py`

- [ ] Remove broad mocked ecommerce tools.
- [ ] Implement the eight group-buy tools from the design spec.
- [ ] Return structured data with IDs, names, counts, rates, amounts, statuses, and timestamps.
- [ ] Use read-only queries and avoid mutating the business database.

### Task 4: Update Demo Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/demo.md`
- Modify: `docs/project-positioning.md`

- [ ] Document that `real-mall-mcp` can use the original MySQL database or a seeded SQLite demo database.
- [ ] Add suggested interview prompts that showcase multi-tool group-buy analysis.

### Task 5: Verify

**Files:**
- No source changes expected.

- [ ] Run `./venv/bin/python -m unittest discover tests -v` from `services/real_mall_mcp`.
- [ ] Run `./venv/bin/python -m unittest discover backend/tests -v` from the repo root.
- [ ] Run `npm run lint` from `frontend`.
- [ ] Run `npm run build` from `frontend`.
- [ ] Run `git diff --check` from the repo root.
