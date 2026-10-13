SELECT
    transaction_id
FROM {{ ref('fact_transactions') }}
WHERE transaction_id IS NULL