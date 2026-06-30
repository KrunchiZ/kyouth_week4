"""Pydantic request/response models for the API."""
from typing import Literal
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
	question: str = Field(..., min_length=1, max_length=500)
	top_k: int = Field(default=3, ge=1, le=17)
	llm_provider: Literal[
		"gemini-3.1-flash-lite",
		"gemini-2.5-flash-lite",
		"gemini-3.5-flash",
		"llama3.2",
		"gemma3:1b",
		] = "llama3.2"


class CardUsed(BaseModel):
	card_title: str
	bank: str


class AskResponse(BaseModel):
	answer: str
	cards_used: list[CardUsed]
	provider: str
	top_k: int


class CardSummary(BaseModel):
	card_title: str
	bank: str


class CardsListResponse(BaseModel):
	cards: list[CardSummary]
	total: int
