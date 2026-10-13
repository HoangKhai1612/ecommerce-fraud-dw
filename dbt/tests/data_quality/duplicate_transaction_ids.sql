SELECT
    transaction_id,
    COUNT(*) AS duplicate_count
FROM {{ ref('fact_transactions') }}
GROUP BY transaction_id
HAVING COUNT(*) > 1