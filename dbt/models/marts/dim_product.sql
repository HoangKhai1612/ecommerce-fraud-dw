WITH source AS (

    SELECT
        product_cd,
        card4

    FROM {{ ref('stg_transactions') }}

),

deduplicated AS (

    SELECT DISTINCT
        product_cd,
        card4

    FROM source

    WHERE product_cd IS NOT NULL

),

numbered AS (

    SELECT
        ROW_NUMBER() OVER (
            ORDER BY product_cd, card4
        )::bigint AS product_key,

        product_cd,
        card4

    FROM deduplicated

)

SELECT
    product_key,
    product_cd,
    card4

FROM numbered