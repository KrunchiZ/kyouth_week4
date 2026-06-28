SELECT 
    SUM(CASE WHEN cashback != 'N/A' THEN 1 ELSE 0 END) AS total_cashback,
    SUM(CASE WHEN petrol != 'N/A' THEN 1 ELSE 0 END) AS total_petrol,
    SUM(CASE WHEN rewards != 'N/A' THEN 1 ELSE 0 END) AS total_rewards,
    SUM(CASE WHEN travel != 'N/A' THEN 1 ELSE 0 END) AS total_travel
FROM credit_cards;