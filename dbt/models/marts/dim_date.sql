WITH date_spine AS (

    SELECT
        generate_series(
            1,
            183
        ) AS transaction_day

)

SELECT
    transaction_day::integer AS date_key,

    transaction_day::integer AS transaction_day,

    ((transaction_day - 1) % 7 + 1)::integer AS day_of_week,

    ((transaction_day - 1) / 7 + 1)::integer AS week_number

FROM date_spine