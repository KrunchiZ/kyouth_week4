"""FastAPI route handlers for the Credit Card RAG Advisor."""
import logging
import json
from pydantic import ValidationError
from fastapi import APIRouter, HTTPException, Request, Query
from config.settings import DB_SERVER_PATH, RATE_LIMITS_PATH
from rag import retriever
from rag.prompts import build_user_prompt
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
	datefmt="%d/%m/%y %H:%M:%S",
)

router = APIRouter()

# Shared rate limiter (initialized once)
_rate_limiter = RateLimiter(RATE_LIMITS_PATH)


# ---------------------------------------------------------------------------
# Helper: fetch all cards from SQLite
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/health")
async def health_check():
	return {"status": "ok"}


@router.get("/cards", response_model=CardsListResponse)
async def list_cards(
	request: Request,
	offset: int = Query(0, ge=0),
	limit: int = Query(17, ge=1, le=100),
):
	async with request.app.state.mcp_client as mcp:
		result = await mcp.call("fetch_all_cards")
	all_cards: list[dict] = (
		json.loads(result.content[0].text) if result.content else []
	)
	total = len(all_cards)
	paginated = all_cards[offset: offset + limit]
	return CardsListResponse(
		cards=[CardSummary(**c) for c in paginated],
		total=total,
	)


@router.get("/cards/{card_title}")
async def get_card(request: Request, card_title: str):
	async with request.app.state.mcp_client as mcp:
		result = await mcp.call("fetch_card_by_title", {"card_title": card_title})
	if not result.content:
		raise HTTPException(status_code=404, detail=f"Card not found: {card_title}")
	return json.loads(result.content[0].text)


@router.get("/banks")
async def list_banks(request: Request):
	async with request.app.state.mcp_client as mcp:
		result = await mcp.call("fetch_all_banks")
	return json.loads(result.content[0].text) if result.content else []


@router.post("/ask", response_model=AskResponse)
async def ask(request: Request, user_request: AskRequest):
	llm_model = user_request.llm_provider

	# 1. Retrieve top-K matching chunks from RAG context
	if retriever._chunks is None:
		raise HTTPException(
			status_code=503,
			detail="RAG context not initialized — server may still be starting",
		)

	matched_chunks = retriever.retrieve_top_context(user_request.question, user_request.top_k)
	matched_card_titles = retriever.extract_card_titles(matched_chunks)

	# 2. Fetch full card details for the matched titles
	async with request.app.state.mcp_client as mcp:
		result = await mcp.call("fetch_all_full_cards")
	all_cards: list[dict] = json.loads(result.content[0].text) if result.content else []
	title_to_card = {c["card_title"]: c for c in all_cards}
	cards = [title_to_card[t] for t in matched_card_titles if t in title_to_card]

	if not cards:
		return AskResponse(
			answer="I couldn't find any matching credit cards in the database.",
			cards_used=[],
			provider=user_request.llm_provider,
			top_k=user_request.top_k,
		)

	# 3. Build prompt
	full_prompt = build_user_prompt(user_request.question, cards)

	print(f"Full prompt sent to LLM:\n{full_prompt}\n")

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

	try:
		return AskResponse(
			answer=answer,
			cards_used=[CardSummary(**{"card_title": c["card_title"], "bank": c["bank"]}) for c in cards],
			provider=user_request.llm_provider,
			top_k=user_request.top_k,
		)
	except ValidationError as code:
		error_messages = [f"{' -> '.join(map(str, err['loc']))}: {err['msg']} ({err['type']})"
			for err in user_request.errors()]
		raise HTTPException(status_code=422, detail=f"{error_messages}")