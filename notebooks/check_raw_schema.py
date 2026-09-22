import sys
sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:postgres@localhost:5432/ecommerce_fraud_dw')

with engine.connect() as conn:
    # Schema info
    cols = conn.execute(text(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = 'raw' AND table_name = 'transactions' "
        "ORDER BY ordinal_position LIMIT 10"
    )).fetchall()
    print("raw.transactions columns (first 10):")
    for c in cols:
        print(f"  {c[0]}: {c[1]}")

    cols2 = conn.execute(text(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = 'raw' AND table_name = 'identity' "
        "ORDER BY ordinal_position LIMIT 10"
    )).fetchall()
    print("\nraw.identity columns (first 10):")
    for c in cols2:
        print(f"  {c[0]}: {c[1]}")

    # Duplicate TransactionID
    dup = conn.execute(text(
        'SELECT COUNT(*) - COUNT(DISTINCT "TransactionID") FROM raw."transactions"'
    )).scalar()
    print(f"\nDuplicate TransactionIDs: {dup}")

    # Full column list
    all_trans_cols = conn.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = 'raw' AND table_name = 'transactions' "
        "ORDER BY ordinal_position"
    )).fetchall()
    print(f"\nTotal transaction columns in DB: {len(all_trans_cols)}")
