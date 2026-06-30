"""FastAPI application entrypoint with RAG lifespan."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastmcp import Client
from api.routes import router
from config.settings import DB_PATH, DB_SERVER_PATH
from rag.retriever import load_cards, initialize_rag_context
from rag.prompt_model import _ensure_gemini_client
from sentence_transformers import SentenceTransformer

logging.basicConfig(
	level=logging.INFO,
	format="[%(asctime)s] | %(levelname)s | %(message)s",
	datefmt="%m/%d/%y %H:%M:%S",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize RAG context once at startup."""
    logging.info("Booting up local RAG matrix...")

    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    cards = load_cards(DB_PATH)
    initialize_rag_context(cards, embedder)

    # Warm up Gemini client so first request doesn't stall
    try:
        _ensure_gemini_client()
    except RuntimeError:
        pass  # API key not available locally — fine for dev

    logging.info("RAG matrix initialized and cached in RAM!")
    app.state.mcp_client = Client(DB_SERVER_PATH)
    await app.state.mcp_client.connect()

    yield

    logging.info("Shutting down RAG server...")
    await app.state.mcp_client.close()


app = FastAPI(title="Credit Card RAG Advisor", version="1.0.0", lifespan=lifespan)

app.include_router(router, prefix="/api/v1")