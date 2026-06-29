from fastapi import APIRouter
from pydantic import BaseModel

from services.backend import ask_ai

router = APIRouter(prefix="/api")

class Question(BaseModel):
    question: str

@router.post("/ask")
async def ask(body: Question):

    return await ask_ai(body.question)