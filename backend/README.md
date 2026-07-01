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

## GET /api/v1/cards?offset=0&limit=10&paginate=true

List all credit cards with pagination.

**Query params:**

- `offset` (int, default 0) — skip this many cards
- `limit` (int, default 10) — max cards to return
- `paginate` (bool, default false) - return by one batch

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
  "total": 2
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
  "features": "Features\nEasy Payment Plan...",
  "min_annual_income": "24000"
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
  "llm_provider": "gemini-3.1-flash-lite"
}
```

**Fields:**

- `question` (string, required, 1–500 chars) — the user's query
- `top_k` (int, default 3, range 1–17) — how many cards to use as context
- `llm_provider` (string, default "gemini-3.1-flash-lite")
  - gemini models
    - `"gemini-3.1-flash-lite"`
    - `"gemini-2.5-flash-lite"`
    - `"gemini-3.5-flash"`
  - ollama models
    - `"llama3.2"`
    - `"gemma3:1b"`

**Response:**

```json
{
  "answer": "AmBank BonusLink Visa Signature\nAmBank\n---\nBased on the available credit cards, the AmBank Cash Rebate Visa Platinum Card offers the best cashback for online shopping. It provides 10% cash rebates capped at RM10 monthly for online transactions, shopping, grocery, dining, and public transport spending — but only when you maintain a minimum monthly balance of RM1,500 or above. For balances below RM1,500, you still earn 0.2% uncapped cashback on all retail spending.\n\nNo other card in the database offers a comparable cashback rate for online transactions.",
  "final_card": {"card_title": "AmBank BonusLink Visa Signature", "bank": "AmBank", ...} // the full detail of the final card in answer in JSON format
  "cards_used": [
    { "card_title": "AmBank Cash Rebate Visa Platinum Card", "bank": "AmBank" },
    { "card_title": "AmBank BonusLink Visa Signature", "bank": "AmBank" }
  ],
  "provider": "gemini-3.1-flash-lite",
  "top_k": 3
}
```

**Fields:**

- `answer` (string) — the AI-generated response
- `final_card` (json) — the final card details chosen in the answer
- `cards_used` (array) — which cards informed the answer
- `provider` (string) — which LLM was used
- `top_k` (int) — how many cards were considered

<br>

## Notes

- **PLEASE USE REVERSE PROXY by making the frontend python script calling the backend url instead of browser HTML/js**
- The `/ask` endpoint may take a few seconds — it retrieves cards, builds a prompt, and calls the LLM.
- The `cards` endpoint returns only title + bank (lightweight). Use `cards/{title}` to get full card details.
