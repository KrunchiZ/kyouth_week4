"""FastAPI route handlers for the Credit Card RAG Advisor."""
import logging
import sqlite3
from fastapi import APIRouter, HTTPException, Query
from config.settings import DB_PATH, RATE_LIMITS_PATH
from rag import retriever
from rag.prompts import SYSTEM_PROMPT, build_user_prompt
from rag.prompt_model import prompt_model
from rag.throttler import RateLimiter
from api.schemas import (
	AskRequest,
	AskResponse,
	CardSummary,
	CardsListResponse,
)

logging.basicConfig(
	level=logging.INFO,
	format="[%(asctime)s] | %(levelname)s | %(message)s",
	datefmt="%m/%d/%y %H:%M:%S",
)

router = APIRouter()

# Shared rate limiter (initialized once)
_rate_limiter = RateLimiter(RATE_LIMITS_PATH)


# ---------------------------------------------------------------------------
# Helper: fetch all cards from SQLite
# ---------------------------------------------------------------------------

def _fetch_all_cards() -> list[dict]:
	with sqlite3.connect(str(DB_PATH)) as conn:
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		cursor.execute("SELECT card_title, bank FROM credit_cards")
		return [dict(row) for row in cursor.fetchall()]


def _fetch_all_full_cards() -> list[dict]:
	with sqlite3.connect(str(DB_PATH)) as conn:
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		cursor.execute("SELECT * FROM credit_cards")
		return [dict(row) for row in cursor.fetchall()]


def _distinct_banks() -> list[str]:
	with sqlite3.connect(str(DB_PATH)) as conn:
		cursor = conn.cursor()
		cursor.execute("SELECT DISTINCT bank FROM credit_cards ORDER BY bank")
		return [row[0] for row in cursor.fetchall()]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/health")
async def health_check():
	return {"status": "ok"}


@router.get("/cards", response_model=CardsListResponse)
async def list_cards(
	offset: int = Query(0, ge=0),
	limit: int = Query(17, ge=1, le=100),
):
	all_cards = _fetch_all_cards()
	total = len(all_cards)
	paginated = all_cards[offset: offset + limit]
	return CardsListResponse(
		cards=[CardSummary(**c) for c in paginated],
		total=total,
	)


@router.get("/cards/{card_title}")
async def get_card(card_title: str):
	cards = _fetch_all_full_cards()
	for card in cards:
		if card["card_title"] == card_title:
			return card
	raise HTTPException(status_code=404, detail=f"Card not found: {card_title}")


@router.get("/banks")
async def list_banks():
	return _distinct_banks()


@router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
	llm_model = request.llm_provider

	# 1. Retrieve top-K matching chunks from RAG context
	if retriever._chunks is None:
		raise HTTPException(
			status_code=503,
			detail="RAG context not initialized — server may still be starting",
		)

	matched_chunks = retriever.retrieve_top_context(request.question, request.top_k)
	card_titles = retriever.extract_card_titles(matched_chunks)

	# 2. Fetch full card details for the matched titles
	all_cards = _fetch_all_full_cards()
	title_to_card = {c["card_title"]: c for c in all_cards}
	cards = [title_to_card[t] for t in card_titles if t in title_to_card]

	if not cards:
		return AskResponse(
			answer="I couldn't find any matching credit cards in the database.",
			cards_used=[],
			provider=request.llm_provider,
			top_k=request.top_k,
		)

	# 3. Build prompt
	user_prompt = build_user_prompt(request.question, cards)
	full_prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"

	# 4. Throttle before calling LLM
	_rate_limiter.wait_if_needed(llm_model, full_prompt)

	# 5. Generate response
	try:
		answer = prompt_model(llm_model, full_prompt)
	except Exception as e:
		logging.error("LLM generation failed: %s", e)
		raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")

	if answer is None:
		raise HTTPException(status_code=503, detail="LLM returned no response.")

	return AskResponse(
		answer=answer,
		cards_used=[CardSummary(**{"card_title": c["card_title"], "bank": c["bank"]}) for c in cards],
		provider=request.llm_provider,
		top_k=request.top_k,
	)
