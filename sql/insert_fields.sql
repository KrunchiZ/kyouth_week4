INSERT OR REPLACE INTO credit_cards (
    card_title,
    bank,
	cashback,
	petrol,
	rewards,
	travel,
	premium_perks,
	balance_transfer,
	easy_payment_plan,
	fees,
	requirements,
	features,
	review,
	keywords,
    content_hash
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);