-- ============================================================
-- STAGING MODEL: TRANSACTIONS
-- ============================================================
--
-- Purpose:
--   1. Read data from RAW through dbt source()
--   2. Convert TEXT values to appropriate PostgreSQL data types
--   3. Standardize column names to snake_case
--   4. Preserve the source transaction identifier
--   5. Add staging audit timestamp
--
-- Output:
--   staging.stg_transactions
--
-- Grain:
--   One row per transaction_id
-- ============================================================

with source as (

    select *
    from {{ source('raw', 'transactions') }}

),

renamed as (

    select

        -- ====================================================
        -- Transaction identifiers / labels
        -- ====================================================

        nullif(trim("TransactionID"), '')::bigint
            as transaction_id,

        nullif(trim("isFraud"), '')::smallint
            as is_fraud,

        nullif(trim("TransactionDT"), '')::bigint
            as transaction_dt,

        nullif(trim("TransactionAmt"), '')::numeric(12, 2)
            as transaction_amt,

        nullif(trim("ProductCD"), '')::varchar(10)
            as product_cd,


        -- ====================================================
        -- Card features
        -- ====================================================

        -- card1 may appear in RAW as values such as:
        -- 315
        -- 315.0
        -- 315.00
        --
        -- Only integer-equivalent numeric values are converted.
        -- Unexpected non-numeric values become NULL rather than
        -- causing the entire dbt model to fail.

        case
            when nullif(trim("card1"), '') is null then null
            when trim("card1") ~ '^[+-]?[0-9]+(\.0+)?$'
                then trim("card1")::numeric::bigint
            else null
        end as card1,

        nullif(trim("card2"), '')::double precision
            as card2,

        nullif(trim("card3"), '')::double precision
            as card3,

        nullif(trim("card4"), '')::varchar(20)
            as card4,

        nullif(trim("card5"), '')::double precision
            as card5,

        nullif(trim("card6"), '')::varchar(20)
            as card6,


        -- ====================================================
        -- Address / distance features
        -- ====================================================

        -- addr1 may appear as 315 or 315.0 in RAW.
        -- Normalize integer-equivalent numeric values to BIGINT.

        case
            when nullif(trim("addr1"), '') is null then null
            when trim("addr1") ~ '^[+-]?[0-9]+(\.0+)?$'
                then trim("addr1")::numeric::bigint
            else null
        end as addr1,

        case
            when nullif(trim("addr2"), '') is null then null
            when trim("addr2") ~ '^[+-]?[0-9]+(\.0+)?$'
                then trim("addr2")::numeric::bigint
            else null
        end as addr2,

        nullif(trim("dist1"), '')::double precision
            as dist1,

        nullif(trim("dist2"), '')::double precision
            as dist2,


        -- ====================================================
        -- Email domain features
        -- ====================================================

        nullif(trim("P_emaildomain"), '')::varchar(255)
            as p_emaildomain,

        nullif(trim("R_emaildomain"), '')::varchar(255)
            as r_emaildomain,


        -- ====================================================
        -- Counting features C1-C14
        -- ====================================================

        {% for i in range(1, 15) %}

        nullif(trim("C{{ i }}"), '')::double precision
            as c{{ i }}{% if not loop.last %},{% endif %}

        {% endfor %},


        -- ====================================================
        -- Time-delta features D1-D15
        -- ====================================================

        {% for i in range(1, 16) %}

        nullif(trim("D{{ i }}"), '')::double precision
            as d{{ i }}{% if not loop.last %},{% endif %}

        {% endfor %},


        -- ====================================================
        -- Match features M1-M9
        -- ====================================================

        {% for i in range(1, 10) %}

        nullif(trim("M{{ i }}"), '')::varchar(10)
            as m{{ i }}{% if not loop.last %},{% endif %}

        {% endfor %},


        -- ====================================================
        -- Vesta features V1-V339
        -- ====================================================

        {% for i in range(1, 340) %}

        nullif(trim("V{{ i }}"), '')::double precision
            as v{{ i }}{% if not loop.last %},{% endif %}

        {% endfor %},


        -- ====================================================
        -- Audit metadata
        -- ====================================================

        current_timestamp as _loaded_at

    from source

)

select *
from renamed