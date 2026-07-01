import httpx
from fastapi import APIRouter, Request
from services.backend import get_cards

router = APIRouter()


async def _get_teaser_cards(target: int = 3, batch_size: int = 10, max_batches: int = 10):
    """Fetch cards in batches (LIMIT/OFFSET) and pick one card per distinct
    bank until we have `target` cards, or the backend runs out of cards."""
    teaser = []
    seen_banks = set()
    offset = 0

    for _ in range(max_batches):
        data = await get_cards(offset=offset, limit=batch_size, paginate=True)
        batch = data.get("cards", [])

        if not batch:
            break

        for card in batch:
            if card["bank"] not in seen_banks:
                seen_banks.add(card["bank"])
                teaser.append(card)
                if len(teaser) == target:
                    return teaser

        offset += batch_size

    return teaser


@router.get("/")
async def landing(request: Request):
    teaser_cards = []

    try:
        teaser_cards = await _get_teaser_cards()
    except (httpx.HTTPError, KeyError, ValueError):
        # Backend hiccup — teaser section just hides itself, rest of the
        # landing page renders fine without it.
        teaser_cards = []

    return request.app.state.templates.TemplateResponse(
        request, "landing.html",
        {
            "teaser_cards": teaser_cards,
        }
    )