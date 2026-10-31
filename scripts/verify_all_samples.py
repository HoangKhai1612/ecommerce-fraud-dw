import urllib.request, json

manifest = json.load(open('evidence/phase_31/dw_demo_manifest.json'))

print("=== FRAUD (expected TP) ===")
for tid in manifest['fraud_samples']:
    with urllib.request.urlopen(f'http://localhost:8000/transactions/{tid}') as r:
        tx = json.loads(r.read().decode('utf-8'))
    tx.pop('_loaded_at', None)
    tx.pop('transaction_key', None)
    req = urllib.request.Request('http://localhost:8000/predictions', data=json.dumps({'mode':'ieee-cis','transaction':tx}).encode('utf-8'), method='POST', headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read().decode('utf-8'))
    status = "OK" if res['is_fraud_predicted'] == 1 else "FAIL"
    print(f"  {tid}: prob={res['fraud_probability']:.4f} label={res['is_fraud_predicted']} [{status}]")

print("=== LEGIT (expected TN) ===")
for tid in manifest['legit_samples']:
    with urllib.request.urlopen(f'http://localhost:8000/transactions/{tid}') as r:
        tx = json.loads(r.read().decode('utf-8'))
    tx.pop('_loaded_at', None)
    tx.pop('transaction_key', None)
    req = urllib.request.Request('http://localhost:8000/predictions', data=json.dumps({'mode':'ieee-cis','transaction':tx}).encode('utf-8'), method='POST', headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read().decode('utf-8'))
    status = "OK" if res['is_fraud_predicted'] == 0 else "FAIL"
    print(f"  {tid}: prob={res['fraud_probability']:.4f} label={res['is_fraud_predicted']} [{status}]")
