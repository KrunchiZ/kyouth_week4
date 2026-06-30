"""Semantic retrieval using SentenceTransformers + sklearn cosine similarity.

Chunks and vectors are built at startup via FastAPI lifespan, not lazily.
"""
import re
import sqlite3
import logging
from pathlib import Path
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

logging.basicConfig(
	level=logging.INFO,
	format="[%(asctime)s] | %(levelname)s | %(message)s",
	datefmt="%d/%m/%y %H:%M:%S",
)

# Global RAG state — populated by FastAPI lifespan at startup
_embedder: SentenceTransformer | None = None
_chunks: list[str] | None = None
_chunk_vectors = None


def load_cards(db_path: Path) -> list[dict]:
	"""Fetch all cards from SQLite."""
	with sqlite3.connect(str(db_path)) as conn:
		cursor = conn.cursor()
		cursor.execute("SELECT * FROM credit_cards")
		columns = [desc[0] for desc in cursor.description]
		return [dict(zip(columns, row)) for row in cursor.fetchall()]


def initialize_rag_context(database_records: list[dict],
						   embedder: SentenceTransformer):
	"""Convert card records into searchable text chunks and pre-compute vectors.

	Stores results in global state for use by ``retrieve_top_context``.
	"""
	global _embedder, _chunks, _chunk_vectors

	_embedder = embedder
	chunks = []
	for card in database_records:
		title = card["card_title"]
		bank = card["bank"]

		for feature in ("cashback", "petrol", "rewards", "travel",
						"premium_perks", "fees", "requirements",
						"balance_transfer", "easy_payment_plan", "features"):
			val = card.get(feature, "N/A")
			if val and val != "N/A":
				clean_val = re.sub(r"\s+", " ", val).strip()
				chunks.append(
					f"Card: {title} ({bank}) | Category: {feature.upper()} | Details: {clean_val}"
				)

	_chunks = chunks
	_chunk_vectors = embedder.encode(chunks, show_progress_bar=False)
	logging.info("RAG context initialized: %d chunks, %d cards", len(chunks),
				len(database_records))


def retrieve_top_context(user_query: str, top_k: int) -> list[str]:
	"""Match the given query against pre-computed chunk vectors using cosine similarity.

	Returns the top-K matching chunk strings.
	"""
	if _embedder is None or _chunks is None:
		logging.error("RAG context not initialized — run lifespan first")
		return []

	query_vector = _embedder.encode([user_query])
	similarity_scores = cosine_similarity(query_vector, _chunk_vectors)[0]
	top_indices = similarity_scores.argsort()[-top_k:][::-1]
	return [_chunks[idx] for idx in top_indices]


def extract_card_titles(matched_chunks: list[str]) -> list[str]:
	"""Extract unique card titles from matched chunks, preserving order.

	Chunks are formatted as: "Card: <title> (<bank>) | Category: ..."
	Returns just the card title without the bank parenthetical.
	"""
	seen_titles = set()
	ordered_titles = []
	for chunk in matched_chunks:
		# "Card: Title (Bank) | Category: ..."
		title_part = chunk.split(" | ")[0]  # "Card: Title (Bank)"
		title = title_part.replace("Card: ", "").rsplit(" (", 1)[0].strip()
		if title not in seen_titles:
			seen_titles.add(title)
			ordered_titles.append(title)
	return ordered_titles
