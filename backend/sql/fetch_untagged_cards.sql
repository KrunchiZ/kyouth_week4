SELECT card_title, bank, requirements
FROM credit_cards
WHERE min_annual_income IS NULL OR TRIM(min_annual_income) = ''
LIMIT :batch_size