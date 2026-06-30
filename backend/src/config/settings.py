"""Application settings — minimal config.
prompt_model.py handles env vars and API keys.
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(
	level=logging.INFO,
	format="[%(asctime)s] | %(levelname)s | %(message)s",
	datefmt="%d/%m/%y %H:%M:%S",
)
logging.getLogger("mcp.server.lowlevel.server").setLevel(logging.WARNING)

load_dotenv()

DEV = os.getenv("DEV") == "true"

DB_PATH = Path("../data/3_gold/credit_cards.db") if DEV else Path("/app/data/3_gold/credit_cards.db")
DB_SERVER_PATH = Path("src/db_server.py")
SQL_PATH = Path("../sql") if DEV else Path("/app/sql")

RATE_LIMITS_PATH = Path(__file__).parent.parent / "rag" / "rate_limits.txt"