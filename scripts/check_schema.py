import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, dbname='ecommerce_fraud_dw', user='postgres', password='@Melons16122005')
cur = conn.cursor()
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='marts' AND table_name='fact_transactions' ORDER BY ordinal_position")
cols = cur.fetchall()
print('Total columns:', len(cols))
for c in cols:
    print(c[0], c[1])
conn.close()
