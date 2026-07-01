from fastapi import APIRouter
from pydantic import BaseModel

from services.backend import ask_ai

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