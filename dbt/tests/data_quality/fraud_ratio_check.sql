WITH fraud_stats AS (
    SELECT
        COUNT(*) AS total_transactions,
        COUNT(*) FILTER (
            WHERE is_fraud = 1
        ) AS fraud_transactions
    FROM {{ ref('fact_transactions') }}
),

fraud_ratio AS (
    SELECT
        total_transactions,
        fraud_transactions,
        fraud_transactions * 100.0
            / NULLIF(total_transactions, 0) AS fraud_percentage
    FROM fraud_stats
)

SELECT
    total_transactions,
    fraud_transactions,
    fraud_percentage
FROM fraud_ratio
WHERE fraud_percentage NOT BETWEEN 2.0 AND 5.0