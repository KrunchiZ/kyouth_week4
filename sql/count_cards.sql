SELECT bank, COUNT(*) AS total_cards
FROM credit_cards
GROUP BY bank
ORDER BY total_cards DESC;