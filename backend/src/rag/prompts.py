"""Prompt templates for the RAG pipeline."""

SYSTEM_PROMPT = (
	"You are a knowledgeable credit card advisor for Malaysian consumers. "
	"You help users find the best credit card based on their needs, preferences, "
	"and financial situation. Be specific, cite card names and banks, and provide "
	"clear recommendations. If the user's question cannot be answered from the "
	"provided card data, say so honestly. Always be helpful and concise."
)

FIELDS_TO_SHOW = [
	"cashback", "petrol", "rewards", "travel",
	"premium_perks", "balance_transfer", "easy_payment_plan",
	"fees", "requirements", "features",
]


def build_user_prompt(question: str, cards: list[dict]) -> str:
	"""Format top-K cards into a structured text payload for the LLM."""
	card_sections = []
	for card in cards:
		section = f"### {card['card_title']} ({card['bank']})\n"
		for field in FIELDS_TO_SHOW:
			value = card.get(field, "")
			if value and value != "N/A":
				label = field.replace("_", " ").title()
				section += f"**{label}**\n{value}\n"
		card_sections.append(section)

	return (
		f"User Question: {question}\n\n"
		f"Available Credit Cards:\n"
		f"{''.join(card_sections)}\n"
		f"Based on the card information above, provide a helpful answer to the "
		f"user's question. Recommend specific cards with reasons. Compare key "
		f"features when relevant."
	)
