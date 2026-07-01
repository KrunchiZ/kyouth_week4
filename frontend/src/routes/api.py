from fastapi import APIRouter, Query
from pydantic import BaseModel

from services.backend import ask_ai, get_cards

router = APIRouter(prefix="/api")


class Question(BaseModel):
    question: str
    top_k: int = 7
    llm_provider: str = "gemini-3.1-flash-lite"


@router.post("/ask")
async def ask(body: Question):
    return await ask_ai(
        question=body.question,
        top_k=body.top_k,
        llm_provider=body.llm_provider,
    )


@router.get("/cards")
async def cards(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    paginate: bool = Query(False),
):
    return await get_cards(offset=offset, limit=limit, paginate=paginate)