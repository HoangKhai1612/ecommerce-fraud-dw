import sys
sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:postgres@localhost:5432/ecommerce_fraud_dw')

with engine.connect() as conn:
    t = conn.execute(text('SELECT COUNT(*) FROM raw."transactions"')).scalar()
    i = conn.execute(text('SELECT COUNT(*) FROM raw."identity"')).scalar()
    print(f'raw.transactions: {t:,} rows')
    print(f'raw.identity: {i:,} rows')

    t_cols = conn.execute(text(
        'SELECT COUNT(*) FROM information_schema.columns '
        'WHERE table_schema = \'raw\' AND table_name = \'transactions\''
    )).scalar()
    i_cols = conn.execute(text(
        'SELECT COUNT(*) FROM information_schema.columns '
        'WHERE table_schema = \'raw\' AND table_name = \'identity\''
    )).scalar()
    print(f'Transactions columns: {t_cols}')
    print(f'Identity columns: {i_cols}')

    print()
    print('--- transactions sample ---')
    sample = conn.execute(text(
        'SELECT "TransactionID", "isFraud", "TransactionAmt", "ProductCD", "TransactionDT" '
        'FROM raw."transactions" LIMIT 3'
    )).fetchall()
    for row in sample:
        print(row)

    print()
    print('--- identity sample ---')
    sample2 = conn.execute(text(
        'SELECT "TransactionID", "DeviceType", "DeviceInfo", "id_01", "id_02" '
        'FROM raw."identity" LIMIT 3'
    )).fetchall()
    for row in sample2:
        print(row)

    nulls = conn.execute(text(
        'SELECT COUNT(*) FROM raw."transactions" WHERE "TransactionID" IS NULL'
    )).scalar()
    print(f'\nNull TransactionID in raw.transactions: {nulls}')

    schemas = conn.execute(text(
        "SELECT schema_name FROM information_schema.schemata "
        "WHERE schema_name IN ('raw', 'staging', 'marts')"
    )).fetchall()
    print(f'Schemas: {[s[0] for s in schemas]}')

    # Check fraud ratio
    fraud_stats = conn.execute(text(
        'SELECT "isFraud", COUNT(*) FROM raw."transactions" GROUP BY "isFraud" ORDER BY "isFraud"'
    )).fetchall()
    print(f'\nFraud distribution:')
    for row in fraud_stats:
        label = "Non-Fraud" if row[0] == '0' else "Fraud" if row[0] == '1' else f"Unknown({row[0]})"
        pct = row[1] / t * 100
        print(f'  {label}: {row[1]:,} ({pct:.2f}%)')
