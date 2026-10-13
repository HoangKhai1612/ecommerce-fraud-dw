WITH device_stats AS (
    SELECT
        COUNT(*) AS total_rows,
        COUNT(*) FILTER (
            WHERE device_type IS NULL
               OR TRIM(device_type) = ''
        ) AS missing_rows
    FROM {{ ref('stg_identity') }}
),

quality_check AS (
    SELECT
        total_rows,
        missing_rows,
        missing_rows * 100.0
            / NULLIF(total_rows, 0) AS missing_percentage
    FROM device_stats
)

SELECT
    total_rows,
    missing_rows,
    missing_percentage
FROM quality_check
WHERE missing_percentage > 30.0