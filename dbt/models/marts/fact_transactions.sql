-- ============================================================
-- FACT MODEL: TRANSACTIONS
-- ============================================================
-- Grain:
--   One row = one transaction
--
-- Natural key:
--   transaction_id
--
-- Surrogate key:
--   transaction_key
--
-- Sources:
--   stg_transactions
--   stg_identity
--   dim_product
--   dim_device
--
-- Purpose:
--   Central fact table for fraud detection and analytics.
-- ============================================================


WITH transactions AS (

    SELECT *
    FROM {{ ref('stg_transactions') }}

),


identity AS (

    SELECT *
    FROM {{ ref('stg_identity') }}

),


product AS (

    SELECT
        product_key,
        product_cd,
        card4
    FROM {{ ref('dim_product') }}

),


device AS (

    SELECT
        device_key,
        device_type,
        device_info
    FROM {{ ref('dim_device') }}

),


joined AS (

    SELECT

        -- ====================================================
        -- TRANSACTION
        -- ====================================================

        t.transaction_id,
        t.is_fraud,
        t.transaction_dt,
        t.transaction_amt,

        -- ====================================================
        -- PRODUCT DIMENSION KEY
        -- ====================================================

        p.product_key,

        -- ====================================================
        -- DEVICE DIMENSION KEY
        -- ====================================================

        d.device_key,

        -- ====================================================
        -- PRODUCT
        -- ====================================================

        t.product_cd,

        t.card1,
        t.card2,
        t.card3,
        t.card4,
        t.card5,
        t.card6,

        -- ====================================================
        -- ADDRESS / DISTANCE
        -- ====================================================

        t.addr1,
        t.addr2,
        t.dist1,
        t.dist2,

        -- ====================================================
        -- EMAIL
        -- ====================================================

        t.p_emaildomain,
        t.r_emaildomain,

        -- ====================================================
        -- COLUMNS C1-C14
        -- ====================================================

        t.c1,
        t.c2,
        t.c3,
        t.c4,
        t.c5,
        t.c6,
        t.c7,
        t.c8,
        t.c9,
        t.c10,
        t.c11,
        t.c12,
        t.c13,
        t.c14,

        -- ====================================================
        -- COLUMNS D1-D15
        -- ====================================================

        t.d1,
        t.d2,
        t.d3,
        t.d4,
        t.d5,
        t.d6,
        t.d7,
        t.d8,
        t.d9,
        t.d10,
        t.d11,
        t.d12,
        t.d13,
        t.d14,
        t.d15,

        -- ====================================================
        -- COLUMNS M1-M9
        -- ====================================================

        t.m1,
        t.m2,
        t.m3,
        t.m4,
        t.m5,
        t.m6,
        t.m7,
        t.m8,
        t.m9,

        -- ====================================================
        -- COLUMNS V1-V339
        -- ====================================================

        {% for i in range(1, 340) %}
        t.v{{ i }},
        {% endfor %}

        -- ====================================================
        -- IDENTITY FEATURES ID01-ID38
        -- ====================================================

        i.id_01,
        i.id_02,
        i.id_03,
        i.id_04,
        i.id_05,
        i.id_06,
        i.id_07,
        i.id_08,
        i.id_09,
        i.id_10,
        i.id_11,
        i.id_12,
        i.id_13,
        i.id_14,
        i.id_15,
        i.id_16,
        i.id_17,
        i.id_18,
        i.id_19,
        i.id_20,
        i.id_21,
        i.id_22,
        i.id_23,
        i.id_24,
        i.id_25,
        i.id_26,
        i.id_27,
        i.id_28,
        i.id_29,
        i.id_30,
        i.id_31,
        i.id_32,
        i.id_33,
        i.id_34,
        i.id_35,
        i.id_36,
        i.id_37,
        i.id_38,

        -- ====================================================
        -- DEVICE ATTRIBUTES
        -- ====================================================

        i.device_type,
        i.device_info,

        -- ====================================================
        -- LOAD METADATA
        -- ====================================================

        t._loaded_at

    FROM transactions t

    LEFT JOIN identity i
        ON t.transaction_id = i.transaction_id

    LEFT JOIN product p
        ON t.product_cd = p.product_cd
        AND t.card4 = p.card4

    LEFT JOIN device d
        ON i.device_type = d.device_type
        AND i.device_info = d.device_info

)


-- ============================================================
-- FINAL FACT TABLE
-- ============================================================

SELECT

    ROW_NUMBER() OVER (
        ORDER BY transaction_id
    )::bigint AS transaction_key,

    transaction_id,

    is_fraud,

    transaction_dt,

    product_key,

    device_key,

    transaction_amt,

    product_cd,

    card1,
    card2,
    card3,
    card4,
    card5,
    card6,

    addr1,
    addr2,

    dist1,
    dist2,

    p_emaildomain,
    r_emaildomain,

    c1,
    c2,
    c3,
    c4,
    c5,
    c6,
    c7,
    c8,
    c9,
    c10,
    c11,
    c12,
    c13,
    c14,

    d1,
    d2,
    d3,
    d4,
    d5,
    d6,
    d7,
    d8,
    d9,
    d10,
    d11,
    d12,
    d13,
    d14,
    d15,

    m1,
    m2,
    m3,
    m4,
    m5,
    m6,
    m7,
    m8,
    m9,

    {% for i in range(1, 340) %}
    v{{ i }},
    {% endfor %}

    id_01,
    id_02,
    id_03,
    id_04,
    id_05,
    id_06,
    id_07,
    id_08,
    id_09,
    id_10,
    id_11,
    id_12,
    id_13,
    id_14,
    id_15,
    id_16,
    id_17,
    id_18,
    id_19,
    id_20,
    id_21,
    id_22,
    id_23,
    id_24,
    id_25,
    id_26,
    id_27,
    id_28,
    id_29,
    id_30,
    id_31,
    id_32,
    id_33,
    id_34,
    id_35,
    id_36,
    id_37,
    id_38,

    device_type,
    device_info,

    _loaded_at

FROM joined