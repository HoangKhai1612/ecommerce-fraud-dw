SELECT
    transaction_id,
    transaction_amt
FROM {{ ref('fact_transactions') }}
WHERE transaction_amt < 0