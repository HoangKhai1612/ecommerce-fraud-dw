import urllib.request, json

manifest = json.load(open('evidence/phase_31/dw_demo_manifest.json'))

for tid in manifest['fraud_samples'][:3]:
    with urllib.request.urlopen(f'http://localhost:8000/transactions/{tid}') as r:
        tx = json.loads(r.read().decode('utf-8'))
    tx.pop('_loaded_at', None)
    tx.pop('transaction_key', None)
    req = urllib.request.Request('http://localhost:8000/predictions', data=json.dumps({'mode':'ieee-cis','transaction':tx}).encode('utf-8'), method='POST', headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read().decode('utf-8'))
    prob = res['fraud_probability']
    label = res['is_fraud_predicted']
    print(f'{tid}: prob={prob:.4f} label={label} (expected 1)')
