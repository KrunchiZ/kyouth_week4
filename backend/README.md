# Backend API — For Frontend Dev

The backend URL is injected as a Docker secret at `/run/secrets/backend_url`. Read it via:

```python
from pathlib import Path

def get_secret(secret_name, default=None):
    secret_path = Path(f"/run/secrets/{secret_name}")
    if secret_path.exists():
        return secret_path.read_text().strip()
    return default
```

Then use `get_secret("backend_url")` to get the backend URL.

<br>

## GET /api/v1/health

Health check.

**Response:**

```json
{ "status": "ok" }
```

<br>

## GET /api/v1/cards?offset=0&limit=17

List all credit cards with pagination.

**Query params:**

- `offset` (int, default 0) — skip this many cards
- `limit` (int, default 17) — max cards to return

**Response:**

```json
{
  "cards": [
    {
        "card_title": "AmBank Cash Rebate Visa Platinum Card",
        "bank": "AmBank"
    },
    {
        "card_title": "Alliance Bank Visa Infinite",
        "bank": "Alliance Bank"
    }
  ],
  "total": 17
}
```

<br>

## GET /api/v1/cards/{card_title}

Get a single card by title (URL-encoded).

**Example:** `GET /api/v1/cards/AmBank%20Cash%20Rebate%20Visa%20Platinum%20Card`

**Response:**

```json
{
  "card_title": "AmBank Cash Rebate Visa Platinum Card",
  "bank": "AmBank",
  "cashback": "Cashback\nEarn 10% cash rebates...",
  "petrol": "N/A",
  "rewards": "N/A",
  "travel": "N/A",
  "premium_perks": "Premium\nThis credit card is available...",
  "balance_transfer": "Balance Transfer\nTransfer your...",
  "easy_payment_plan": "Easy Payment Plans\nChoose from...",
  "fees": "Fees & Charges\nAnnual Fee RM0...",
  "requirements": "Requirements\nMinimum Annual Income RM24,000...",
  "features": "Features\nEasy Payment Plan..."
}
```

All fields are plain text strings. `N/A` means that category doesn't apply to this card. Tables within the original HTML are converted to Markdown format.

<br>

## GET /api/v1/banks

List distinct banks.

**Response:**

```json
["AmBank", "Alliance Bank"]
```

<br>

## POST /api/v1/ask

The RAG chat endpoint. Sends a question and gets an AI-generated answer backed by the credit card database.

**Request body:**

```json
{
  "question": "Which card has the best cashback for online shopping?",
  "top_k": 3,
  "llm_provider": "gemini"
}
```

**Fields:**

- `question` (string, required, 1–500 chars) — the user's query
- `top_k` (int, default 3, range 1–17) — how many cards to use as context
- `llm_provider` (string, default "gemini") — `"gemini"` or `"ollama"`

**Response:**

```json
{
  "answer": "Based on the available credit cards, the AmBank Cash Rebate Visa Platinum Card offers the best cashback for online shopping. It provides 10% cash rebates capped at RM10 monthly for online transactions, shopping, grocery, dining, and public transport spending — but only when you maintain a minimum monthly balance of RM1,500 or above. For balances below RM1,500, you still earn 0.2% uncapped cashback on all retail spending.\n\nNo other card in the database offers a comparable cashback rate for online transactions.",
  "cards_used": [
    { "card_title": "AmBank Cash Rebate Visa Platinum Card", "bank": "AmBank" },
    { "card_title": "AmBank BonusLink Visa Signature", "bank": "AmBank" }
  ],
  "provider": "gemini",
  "top_k": 3
}
```

**Fields:**

- `answer` (string) — the AI-generated response
- `cards_used` (array) — which cards informed the answer
- `provider` (string) — which LLM was used
- `top_k` (int) — how many cards were considered

<br>

## Notes

- The `/ask` endpoint may take a few seconds — it retrieves cards, builds a prompt, and calls the LLM.
- If `llm_provider` is set to `"ollama"`, the request goes through the local Ollama service (port 11434). If set to `"gemini"`, it uses the Gemini cloud API.
- The `cards` endpoint returns only title + bank (lightweight). Use `cards/{title}` to get full card details.
