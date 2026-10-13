SELECT
    transaction_id,
    is_fraud
FROM {{ ref('fact_transactions') }}
WHERE is_fraud NOT IN (0, 1)
   OR is_fraud IS NULL
   