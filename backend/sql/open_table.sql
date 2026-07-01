CREATE TABLE IF NOT EXISTS credit_cards (
    card_title			TEXT PRIMARY KEY,
    bank				TEXT NOT NULL,
	cashback			TEXT NOT NULL,
	petrol				TEXT NOT NULL,
	rewards				TEXT NOT NULL,
	travel				TEXT NOT NULL,
	premium_perks		TEXT NOT NULL,
	balance_transfer	TEXT NOT NULL,
	easy_payment_plan	TEXT NOT NULL,
	fees				TEXT NOT NULL,
	requirements		TEXT NOT NULL,
	features			TEXT NOT NULL,
	min_annual_income	TEXT,
    content_hash		TEXT NOT NULL
);