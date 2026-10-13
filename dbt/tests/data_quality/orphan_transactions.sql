SELECT
    f.transaction_id
FROM {{ ref('fact_transactions') }} AS f
LEFT JOIN {{ ref('stg_transactions') }} AS s
    ON f.transaction_id = s.transaction_id
WHERE s.transaction_id IS NULL