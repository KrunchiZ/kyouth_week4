# Due to some path issues,
# please run this script in the backend directory
# "uv run src/tag_data.py"

import asyncio
import math
import json
import logging
import os
import sys
from pathlib import Path
from fastmcp import Client
from rag.prompt_model import prompt_model
from rag.throttler import RateLimiter
from config.settings import DB_PATH, DB_SERVER_PATH, RATE_LIMITS_PATH

_rate_limiter = RateLimiter(RATE_LIMITS_PATH)

logging.basicConfig(
	level=logging.INFO,
	format="[%(asctime)s] | %(levelname)s | %(message)s",
	datefmt="%m/%d/%y %H:%M:%S",
)

# ---------------------------------------------------------------------------
# ─── GLOBAL CONFIGURATION ───────────────────────────────────────────────────
# ---------------------------------------------------------------------------

DEBUG = True
LOCAL_MODEL = False

# model passed to prompt_model()
OLLAMA_MODELS = [
	"llama3.2",
	"gemma3:1b",
]

GEMINI_MODELS = [
	"gemini-3.1-flash-lite",
	"gemini-2.5-flash-lite",
	"gemini-3.5-flash",
]

MODEL = OLLAMA_MODELS[0] if LOCAL_MODEL else GEMINI_MODELS[0]

TEMPERATURE = 0.0
TOP_P = 0.95

# Hypothetical local model rate limits (local models not in rate_limits.txt)
# Formula: batch_size = floor(LOCAL_TPM / AVG_TOKENS_PER_JOB)
LOCAL_RPM = 60
LOCAL_TPM = 250_000

MAX_RETRIES				= 3
BACKOFF_BASE_SECONDS	= 2.0        # seconds; doubles each retry

PROMPT_LINES = [
	"Extract the minimum annual income from the requirements of each credit card.",
	"Reply ONLY in this JSON format, one line per card, no other explanation:",
	"<card_title>: <min_annual_income>",
	"",
	"Rules:",
	"- No other text or explanation; only the JSON lines.",
	"- No markdown, no code blocks, no quotes, no extra characters.",
	"- If the card has no minimum income requirement, look for the specific condition.",
	"",
	"Example:",
	"AmBank Basic Credit Card: 'N/A'",
	"AmBank Visa Credit Card: 48000",
	"Alliance Bank Visa Infinite Business Credit Card: 'Invitation only'",
	"",
	"--- DATA STARTS HERE ---",
]

# ---------------------------------------------------------------------------
# ─── MAIN CLI ENTRY POINT ───────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def main():
	if not DB_PATH.exists():
		logging.warning(f"Input path not found: {DB_PATH}")
		sys.exit(1)
	if not os.access(DB_PATH, os.R_OK):
		logging.warning(f"Input path not readable: {DB_PATH}")
		sys.exit(1)
	tag_data()


# ---------------------------------------------------------------------------
# ─── CORE TAG_DATA ──────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def tag_data():
	try:
		asyncio.run(_tag_data_async())
	except Exception as code:
		logging.error(f"Fatal error: {code}")


async def _tag_data_async():
	async with Client(DB_SERVER_PATH) as mcp:
		b_idx = 0
		while True:
			batch_size, retry_delay = await compute_batch_params(mcp)

			untagged_result = await mcp.call_tool("fetch_untagged_cards", {"batch_size": batch_size})
			batch: list[dict] = (
				json.loads(untagged_result.content[0].text) if untagged_result.content else []
			)
			if not batch:
				break

			expected_ids = [card["card_title"] for card in batch]
			prompt = _build_prompt(batch, PROMPT_LINES)
			parsed: dict[str, str] = {}
			for attempt in range(1, MAX_RETRIES + 1):
				try:
					raw = prompt_model(MODEL, prompt, temperature=TEMPERATURE, top_p=TOP_P)
					if not raw:
						raise ValueError("Empty response from model")
					parsed = _parse_response(raw, expected_ids)
					if len(parsed) != len(batch):
						raise ValueError(
							"Mismatch between batch size and response")
					break

				except Exception as code:
					logging.error(f"[Batch {b_idx}] Attempt {attempt} failed: {code}"
						f"Retrying in {retry_delay:.1f}s [{attempt+1}/{MAX_RETRIES}]")
					if attempt < MAX_RETRIES:
						await asyncio.sleep(retry_delay
							* (BACKOFF_BASE_SECONDS ** (attempt - 1)))
					else:
						logging.error(f"[Batch {b_idx}] All {MAX_RETRIES} attempts "
							"failed — skipping batch.")

			for card in batch:
				min_annual_income = parsed.get(card["card_title"], "")
				if not min_annual_income:
					continue
				ok = await mcp.call_tool(
					"update_min_annual_income",
					{"card_title": card["card_title"], "min_annual_income": min_annual_income}
				)
				if ok:
					logging.info(f"Analyzed {card['card_title']}: {min_annual_income}")
			b_idx += 1

		if b_idx == 0:
			logging.info("No cards to tag")


# ---------------------------------------------------------------------------
# ─── BATCH SIZE & RETRY DELAY ───────────────────────────────────────────────
# ---------------------------------------------------------------------------

async def compute_batch_params(mcp: Client) -> tuple[int, float]:
	limits: dict[str, int] = _parse_rate_limits(RATE_LIMITS_PATH)
	m   = limits.get(MODEL, {})
	tpm = m.get("tpm", LOCAL_TPM)
	rpm = m.get("rpm", LOCAL_RPM)
	avg_fees_length = await mcp.call_tool("count_avg_fees_length", {})
	card_count = await mcp.call_tool("count_total_cards", {})
	est_tokens_per_card = math.ceil((
		json.loads(avg_fees_length.content[0].text)
		if avg_fees_length else 200) / 4 + 300
	)
	job_count = int(json.loads(card_count.content[0].text)) if card_count else 0

	batch_size = (math.ceil(job_count / 2) if job_count <= 30
		else min(tpm // est_tokens_per_card // rpm,
			math.ceil(job_count / (rpm // MAX_RETRIES))))
	retry_delay = math.ceil(60 / rpm)
	return batch_size, float(retry_delay)


def _parse_rate_limits(path: Path) -> dict[str, dict]:
	limits: dict[str, dict] = {}
	if not path.exists():
		return limits
	for line in path.read_text().splitlines():
		line = line.strip()
		if not line or line.startswith("#"):
			continue
		parts = line.split()
		if len(parts) < 4:
			continue
		model, rpm_s, tpm_s, rpd_s = parts[0], parts[1], parts[2], parts[3]
		limits[model] = {
			"rpm": _parse_num(rpm_s),
			"tpm": _parse_num(tpm_s),
			"rpd": _parse_num(rpd_s),
		}
	return limits


def _parse_num(s: str) -> int:
	s = s.upper().replace(",", "")
	if s.endswith("M"):
		return int(float(s[:-1]) * 1_000_000)
	if s.endswith("K"):
		return int(float(s[:-1]) * 1_000)
	return int(s)


# ---------------------------------------------------------------------------
# ─── PROMPT BUILDER ─────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def _build_prompt(cards: list[dict], prompt_lines: list[str]) -> str:
	# Compact prompt — one line per card, no markdown or chain-of-thought.
	for card in cards:
		requirement = (card.get("requirements").replace("\n", " ") or "").strip()
		prompt_lines.append(f'{card["card_title"]}\n{card["bank"]}\n'
					 f'\n{requirement}\n---')
	return "\n".join(prompt_lines)


# ---------------------------------------------------------------------------
# ─── RESPONSE PARSING ───────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def _parse_response(raw: str, expected_ids: list[str]) -> dict[str, str]:
	result: dict[str, str] = {}
	for line in raw.splitlines():
		line = line.strip()
		if not line or ":" not in line:
			continue
		card_title, _, tags = line.partition(":")
		card_title = card_title.strip().strip("\"\'[]").strip()
		if card_title in expected_ids:
			result[card_title] = tags.strip().strip("\"\',[]").strip()
	return result


if __name__ == "__main__":
	main()