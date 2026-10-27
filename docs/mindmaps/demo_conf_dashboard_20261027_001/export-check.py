import csv,io,json
from pathlib import Path
import workflow,data
workflow.FILE=Path('test-state.json');before=workflow.FILE.read_bytes();raw=data.accounting_csv();rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig')),delimiter=';'));d=data.dashboard()
assert workflow.FILE.read_bytes()==before
assert len({r['id'] for r in rows})==len(rows)
parents={r['id']:r for r in rows if r['record_type'] in {'invoice','sale'}}
for r in rows:
 assert r['original_invoice'] in parents
 assert r['source_sha256'] and r['required_mappings']
 if r['parent_payment']:assert any(p['id']==r['parent_payment'] and p['record_type']=='payment' for p in rows)
net=sum(int(r['net_cents']) for r in rows if r['record_type'] in {'invoice','sale','credit','sale_return'})
assert net==d['revenue_cents'],(net,d['revenue_cents'])
received=sum(int(r['total_cents']) for r in rows if r['record_type'] in {'payment','payment_reversal','refund','sale_payment','sale_refund'})
assert received==d['payments_cents'],(received,d['payments_cents'])
for ident,parent in parents.items():
 records=[r for r in rows if r['original_invoice']==ident]
 effect=sum(int(r['total_cents']) for r in records if r['record_type'] in {'payment','payment_reversal','refund','sale_payment','sale_refund'})
 assert effect==int(parent['received_cents'])-int(parent['refund_cents'])
 credits=-sum(int(r['total_cents']) for r in records if r['record_type'] in {'credit','sale_return'})
 assert credits==int(parent['credit_cents'])
 assert int(parent['total_cents'])-credits-effect==int(parent['open_cents'])
Path('export-sample.csv').write_bytes(raw)
Path('export-results.json').write_text(json.dumps(dict(result='PASS',rows=len(rows),parents=len(parents),net_revenue_cents=net,net_receipts_cents=received,checks=['unique ids','every correction linked','all invoice/sale balances reconcile','dashboard revenue equals export','dashboard receipts equals export','mapping and missing fields explicit','download does not mutate state'],external_import='NOT TESTED — no external package access'),ensure_ascii=False,indent=2))
print('PASS',len(rows),'export rows, all amounts and relationships reconcile')
