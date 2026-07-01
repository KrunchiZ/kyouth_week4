import httpx
from fastapi import APIRouter, Request
from services.backend import get_cards, get_banks, get_card

router = APIRouter()


async def _fetch_all_cards_summary(batch_size: int = 10):
    """Fetch all CardSummary records in batches using LIMIT/OFFSET."""
    all_cards = []
    offset = 0
    for _ in range(50):  # safety cap
        data = await get_cards(offset=offset, limit=batch_size, paginate=True)
        batch = data.get("cards", [])
        if not batch:
            break
        all_cards.extend(batch)
        if len(batch) < batch_size:
            break
        offset += batch_size
    return all_cards


@router.get("/dashboard")
async def dashboard(request: Request):
    cards = []
    banks = []
    bank_counts = {}
    error = None

    try:
        cards = await _fetch_all_cards_summary()
        for card in cards:
            bank = card["bank"]
            bank_counts[bank] = bank_counts.get(bank, 0) + 1
    except httpx.ConnectError:
        error = "Could not connect to the card service. Please try again later."
    except httpx.HTTPStatusError as e:
        error = f"Card service returned an error (status {e.response.status_code})."
    except httpx.TimeoutException:
        error = "The card service took too long to respond."
    except (KeyError, ValueError):
        error = "Received unexpected data from the card service."

    try:
        banks = await get_banks()
    except (httpx.HTTPError, KeyError, ValueError):
        banks = []

    return request.app.state.templates.TemplateResponse(
        request, "dashboard.html",
        {
            "cards":       cards,
            "banks":       banks,
            "bank_counts": bank_counts,
            "error":       error,
        }
    )


@router.get("/dashboard/{card_title}")
async def card_detail(request: Request, card_title: str):
    card = None
    error = None
    status_code = 200

    try:
        card = await get_card(card_title)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            error = f'No card found matching "{card_title}".'
        else:
            error = f"Card service returned an error (status {e.response.status_code})."
        status_code = e.response.status_code
    except httpx.ConnectError:
        error = "Could not connect to the card service. Please try again later."
        status_code = 503
    except httpx.TimeoutException:
        error = "The card service took too long to respond."
        status_code = 504
    except (KeyError, ValueError):
        error = "Received unexpected data from the card service."
        status_code = 502

    return request.app.state.templates.TemplateResponse(
        request, "card_detail.html",
        {
            "card":  card,
            "error": error,
        },
        status_code=status_code
    )