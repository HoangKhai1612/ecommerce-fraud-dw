WITH distribution AS (
    SELECT
        COUNT(*) AS total_rows,
        COUNT(*) FILTER (WHERE is_fraud = 0) AS non_fraud_rows,
        COUNT(*) FILTER (WHERE is_fraud = 1) AS fraud_rows
    FROM {{ ref('fact_transactions') }}
)

SELECT
    total_rows,
    non_fraud_rows,
    fraud_rows
FROM distribution
WHERE non_fraud_rows + fraud_rows <> total_rows