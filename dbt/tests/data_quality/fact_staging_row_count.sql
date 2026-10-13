WITH counts AS (
    SELECT
        (SELECT COUNT(*)
         FROM {{ ref('stg_transactions') }}) AS staging_count,

        (SELECT COUNT(*)
         FROM {{ ref('fact_transactions') }}) AS fact_count
)

SELECT
    staging_count,
    fact_count
FROM counts
WHERE staging_count <> fact_count