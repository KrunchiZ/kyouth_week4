"""FastAPI route handlers for the Credit Card RAG Advisor."""
import logging
import json
from pydantic import ValidationError
from fastapi import APIRouter, HTTPException, Request, Query
from config.settings import RATE_LIMITS_PATH
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


router = APIRouter()

# Shared rate limiter (initialized once)
_rate_limiter = RateLimiter(RATE_LIMITS_PATH)


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
	limit: int = Query(10, ge=1, le=100),
	paginate: bool = Query(False, description="Whether to paginate the results"),
):
	mcp = request.app.state.mcp_client
	index = offset
	cards: list[dict] = []
	while True:
		result = await mcp.call_tool("fetch_all_cards", {"offset": index, "limit": limit})
		current_batch: list[dict] = json.loads(result.content[0].text) if result.content else []
		if not current_batch:
			break
		cards.extend(current_batch)
		if paginate or len(current_batch) < limit:
			break
		index += limit
	return CardsListResponse(
		cards=[CardSummary(**c) for c in cards],
		total=len(cards),
	)


@router.get("/cards/{card_title}")
async def get_card(request: Request, card_title: str):
	mcp = request.app.state.mcp_client
	result = await mcp.call_tool("fetch_card_by_title", {"card_title": card_title})
	if not result.content:
		raise HTTPException(status_code=404, detail=f"Card not found: {card_title}")
	return json.loads(result.content[0].text)


@router.get("/banks")
async def list_banks(request: Request):
	mcp = request.app.state.mcp_client
	result = await mcp.call_tool("fetch_all_banks")
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
	mcp = request.app.state.mcp_client
	offset = 0
	cards: list[dict] = []
	while True:
		result = await mcp.call_tool("fetch_all_cards", {"offset": offset, "limit": 10})
		current_batch: list[dict] = json.loads(result.content[0].text) if result.content else []
		if not current_batch:
			break
		title_to_card = {c["card_title"]: c for c in current_batch}
		matched_cards = [title_to_card[t] for t in matched_card_titles.keys() if t in title_to_card]
		cards.extend(matched_cards)
		if len(current_batch) < 10:
			break
		offset += 10

	if not cards:
		return AskResponse(
			answer="I couldn't find any matching credit cards in the database.",
			final_card=None,
			cards_used=[],
			provider=user_request.llm_provider,
			top_k=user_request.top_k,
			match_scores=0
		)

	# 3. Build prompt
	full_prompt = build_user_prompt(user_request.question, cards)

	for i in range(3):  # Retry up to 3 times
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

		final_card = answer.splitlines()[0].strip()
		if final_card and final_card != "N/A":
			final_card = json.loads(
				(await mcp.call_tool("fetch_card_by_title", {"card_title": final_card}))
				.content[0].text
			)
			break
		elif final_card == "N/A":
			final_card = {"card_title": "N/A", "bank": "N/A", "min_annual_income": "N/A"}
			break
		else:
			if i < 2:
				logging.warning("LLM response did not contain a valid card title. Retrying...")
				continue
			raise HTTPException(status_code=503,
				detail="LLM response did not contain a valid card title after 3 attempts.")
	try:
		match_scores = (matched_card_titles[final_card["card_title"]]
			if final_card and final_card["card_title"] in matched_card_titles
			else 0
		)
		return AskResponse(
			answer=answer,
			final_card=final_card,
			cards_used=[CardSummary(**{
					"card_title": c["card_title"],
					"bank": c["bank"],
					"min_annual_income": c["min_annual_income"]
				}) for c in cards
			],
			provider=user_request.llm_provider,
			top_k=user_request.top_k,
			match_scores=match_scores
		)
	except ValidationError as code:
		error_messages = [f"{' -> '.join(map(str, err['loc']))}: {err['msg']} ({err['type']})"
			for err in code.errors()]
		raise HTTPException(status_code=422, detail=f"{error_messages}")