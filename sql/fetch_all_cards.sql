SELECT
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
    min_annual_income
FROM credit_cards
LIMIT :limit
OFFSET :offset