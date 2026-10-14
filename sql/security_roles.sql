-- PHASE 28: Database least-privilege permissions
-- Run as a database administrator.
-- Review the existing owners and grants before execution.

-- AI Assistant: read marts only.
GRANT CONNECT ON DATABASE ecommerce_fraud_dw TO ai_assistant_ro;
GRANT USAGE ON SCHEMA marts TO ai_assistant_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA marts TO ai_assistant_ro;

-- Remove write privileges if previously granted.
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER
ON ALL TABLES IN SCHEMA marts FROM ai_assistant_ro;

REVOKE CREATE ON SCHEMA marts FROM ai_assistant_ro;

-- IMPORTANT:
-- ALTER DEFAULT PRIVILEGES applies to objects created by the
-- specified owner. Replace dw_owner with the actual object owner.
ALTER DEFAULT PRIVILEGES FOR ROLE dw_owner IN SCHEMA marts
GRANT SELECT ON TABLES TO ai_assistant_ro;

-- Do not grant CREATE on application schemas to the AI role.
-- Do not grant access to raw or staging unless explicitly required.

-- Verification queries:
SELECT
    grantee,
    table_schema,
    privilege_type
FROM information_schema.role_table_grants
WHERE grantee = 'ai_assistant_ro'
ORDER BY table_schema, privilege_type;

SELECT
    nspname AS schema_name,
    has_schema_privilege(
        'ai_assistant_ro', nspname, 'USAGE'
    ) AS can_use_schema,
    has_schema_privilege(
        'ai_assistant_ro', nspname, 'CREATE'
    ) AS can_create_objects
FROM pg_namespace
WHERE nspname IN ('raw', 'staging', 'marts');


-- Before running: replace dw_owner with the actual owner of tables in marts.
-- Check with:
-- SELECT
--     schemaname,
--     tablename,
--     tableowner
-- FROM pg_tables
-- WHERE schemaname IN ('raw', 'staging', 'marts')
-- ORDER BY schemaname, tablename;


-- Important notes:
-- REVOKE above does not automatically revoke privileges inherited from other roles.
-- You must check role membership and direct grants.
-- If the account has SUPERUSER, revoking table privileges is not sufficient to restrict it.
-- ALTER DEFAULT PRIVILEGES only affects objects created after this command by the specified owner;
-- configure correspondingly for each actual owner.
-- Do not grant CREATEDB to etl_user or airflow_user if the current architecture doesn't require it.
-- Airflow metadata database should have a separate account, isolated from the Data Warehouse access account.

-- Read-only verification (run as ai_assistant_ro in test environment):
-- Must succeed if table exists and has been granted:
-- SELECT transaction_id FROM marts.fact_transactions LIMIT 1;

-- Must be rejected by PostgreSQL:
-- UPDATE marts.fact_transactions SET transaction_id = transaction_id WHERE FALSE;