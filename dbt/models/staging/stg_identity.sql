-- ============================================================
-- STAGING MODEL: IDENTITY
-- ============================================================
--
-- Purpose:
--   1. Read identity data from RAW
--   2. Standardize column names
--   3. Convert values to appropriate PostgreSQL types
--   4. Preserve transaction_id for downstream relationship
--   5. Add staging audit timestamp
--
-- Output:
--   staging.stg_identity
--
-- Grain:
--   One row per identity record associated with transaction_id
-- ============================================================

with source as (

    select *
    from {{ source('raw', 'identity') }}

),

renamed as (

    select

        -- ====================================================
        -- Transaction identifier
        -- ====================================================

        nullif(trim("TransactionID"), '')::bigint
            as transaction_id,


        -- ====================================================
        -- Identity numerical features: id_01-id_11
        -- ====================================================

        {% for i in range(1, 12) %}

        nullif(
            trim("id_{{ '%02d' | format(i) }}"),
            ''
        )::double precision
            as id_{{ '%02d' | format(i) }}{% if not loop.last %},{% endif %}

        {% endfor %},


        -- ====================================================
        -- Identity mixed-type features: id_12-id_38
        --
        -- These fields may contain heterogeneous values.
        -- They are therefore preserved as VARCHAR in staging
        -- instead of forcing potentially unsafe numeric casts.
        -- ====================================================

        {% for i in range(12, 39) %}

        nullif(
            trim("id_{{ '%02d' | format(i) }}"),
            ''
        )::varchar(50)
            as id_{{ '%02d' | format(i) }}{% if not loop.last %},{% endif %}

        {% endfor %},


        -- ====================================================
        -- Device information
        -- ====================================================

        nullif(trim("DeviceType"), '')::varchar(20)
            as device_type,

        nullif(trim("DeviceInfo"), '')::varchar(255)
            as device_info,


        -- ====================================================
        -- Audit metadata
        -- ====================================================

        current_timestamp as _loaded_at

    from source

)

select *
from renamed