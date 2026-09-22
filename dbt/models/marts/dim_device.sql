WITH source AS (

    SELECT
        device_type,
        device_info

    FROM {{ ref('stg_identity') }}

),

deduplicated AS (

    SELECT DISTINCT
        device_type,
        device_info

    FROM source

    WHERE device_type IS NOT NULL

),

numbered AS (

    SELECT
        ROW_NUMBER() OVER (
            ORDER BY device_type, device_info
        )::bigint AS device_key,

        device_type,
        device_info

    FROM deduplicated

)

SELECT
    device_key,
    device_type,
    device_info

FROM numbered