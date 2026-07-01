from pathlib import Path
import httpx


def get_secret(secret_name: str, default: str | None = None):
    """Read a Docker secret."""
    secret_path = Path(f"/run/secrets/{secret_name}")

    if secret_path.exists():
        return secret_path.read_text().strip()
    else:
            if default is not None:
                return default
            raise FileNotFoundError(f"Secret {secret_name} not found at {secret_path}")

BACKEND_URL = get_secret(
    "backend_url",
    default="http://localhost:8001"
)


async def get_health():
    """GET /api/v1/health"""

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BACKEND_URL}/api/v1/health"
        )

    response.raise_for_status()

    return response.json()


async def get_cards(offset: int = 0, limit: int = 17):
    """GET /api/v1/cards"""

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BACKEND_URL}/api/v1/cards",
            params={
                "offset": offset,
                "limit": limit,
            },
        )

    response.raise_for_status()

    return response.json()


async def get_card(card_title: str):
    """GET /api/v1/cards/{card_title}"""

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BACKEND_URL}/api/v1/cards/{card_title}"
        )

    response.raise_for_status()

    return response.json()


async def get_banks():
    """GET /api/v1/banks"""

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BACKEND_URL}/api/v1/banks"
        )

    response.raise_for_status()

    return response.json()


async def ask_ai(
    question: str,
    top_k: int = 3,
    llm_provider: str = "gemini-3.1-flash-lite",
):
    """POST /api/v1/ask"""

    payload = {
        "question": question,
        "top_k": top_k,
        "llm_provider": llm_provider,
    }

    async with httpx.AsyncClient(timeout=400) as client:
        response = await client.post(
            f"{BACKEND_URL}/api/v1/ask",
            json=payload,
        )

    response.raise_for_status()

    return response.json()