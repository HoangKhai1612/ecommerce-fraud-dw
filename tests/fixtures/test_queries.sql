-- Valid queries for security testing
SELECT COUNT(*) FROM marts.fact_transactions;
SELECT * FROM marts.fact_transactions LIMIT 5;
SELECT is_fraud, COUNT(*) FROM marts.fart_transactions GROUP BY is_fraud;

-- Invalid queries (for validation testing)
DELETE FROM marts.fact_transactions;
UPDATE marts.fact_transactions SET is_fraud = 0;
INSERT INTO marts.fact_transactions VALUES (1);
DROP TABLE marts.fact_transactions;
SELECT * FROM public.users;
SELECT * FROM fact_transactions;