"""
db_server.py — FastMCP server for all SQLite DB operations.
All queries are loaded from ./sql/*.sql files.
Run standalone or used as a stdio MCP server by tag_data.py.
"""

import sqlite3
from pathlib import Path
from fastmcp import FastMCP
from config.settings import SQL_PATH, DB_PATH

BASE = Path(SQL_PATH)
COUNT_CARDS	= BASE / "count_cards.sql"
COUNT_CATEGORIES = BASE / "count_categories.sql"
COUNT_TOTAL_CARDS = BASE / "count_total_cards.sql"
FETCH_ALL_CARDS = BASE / "fetch_all_cards.sql"
FETCH_CARD_BY_TITLE = BASE / "fetch_card_by_title.sql"
DISTINCT_BANKS = BASE / "distinct_banks.sql"


# MCP server
mcp = FastMCP("SQLite-Service")


def _load_sql(path: Path) -> str:
	return path.read_text(encoding="utf-8").strip()


def _connect() -> sqlite3.Connection:
	conn = sqlite3.connect(DB_PATH)
	conn.row_factory = sqlite3.Row
	return conn


# ----------------------------------------------------------------------------
# mcp tools
# ---------------------------------------------------------------------------

@mcp.tool()
def count_total_cards() -> int:
	sql = _load_sql(COUNT_TOTAL_CARDS)
	with _connect() as conn:
		result = conn.execute(sql).fetchone()
	return int(result[0]) if result else 0


@mcp.tool()
def count_cards() -> list[dict]:
	sql = _load_sql(COUNT_CARDS)
	with _connect() as conn:
		cursor = conn.cursor()
		cursor.execute(sql)
		return [dict(row) for row in cursor.fetchall()]


@mcp.tool()
def count_categories() -> dict:
	sql = _load_sql(COUNT_CATEGORIES)
	with _connect() as conn:
		cursor = conn.cursor()
		cursor.execute(sql)
		row = cursor.fetchone()
		col = [description[0] for description in cursor.description]
		return dict(zip(col, row)) if row else {}


@mcp.tool()
def fetch_all_cards(batch_size: int) -> list[dict]:
	sql = _load_sql(FETCH_ALL_CARDS)
	with _connect() as conn:
		cursor = conn.cursor()
		cursor.execute(sql)
		return [dict(row) for row in cursor.fetchall()]


@mcp.tool()
def fetch_card_by_title(card_title: str) -> list[dict]:
	sql = _load_sql(FETCH_CARD_BY_TITLE)
	with _connect() as conn:
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		cursor.execute(sql, {"card_title": card_title})
		return [dict(row) for row in cursor.fetchall()]


@mcp.tool()
def distinct_banks() -> list[str]:
	sql = _load_sql(DISTINCT_BANKS)
	with _connect() as conn:
		cursor = conn.cursor()
		cursor.execute(sql)
		return [row[0] for row in cursor.fetchall()]


if __name__ == "__main__":
	mcp.run()