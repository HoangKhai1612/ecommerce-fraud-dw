SELECT
    COUNT(*) AS row_count
FROM {{ ref('fact_transactions') }}
HAVING COUNT(*) = 0