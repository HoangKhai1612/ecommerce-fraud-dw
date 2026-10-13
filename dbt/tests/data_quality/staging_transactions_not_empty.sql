SELECT
    COUNT(*) AS row_count
FROM {{ ref('stg_transactions') }}
HAVING COUNT(*) = 0