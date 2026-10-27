import unittest,json,hashlib,tempfile,copy,csv,io
from pathlib import Path
import workflow,data,accounting
ROOT=Path(__file__).parent
class AccountingAdapter(unittest.TestCase):
 def test_package_neutral_export_preserves_existing_contract_and_does_not_mutate(self):
  with tempfile.TemporaryDirectory() as tmp:
   workflow.FILE=Path(tmp)/'workflow.json';workflow.FILE.write_bytes((ROOT/'live-reference.json').read_bytes());before=workflow.FILE.read_bytes();snapshot=data.accounting_snapshot();original=copy.deepcopy(snapshot)
   exported=accounting.export_csv(snapshot);self.assertEqual(snapshot,original);self.assertEqual(workflow.FILE.read_bytes(),before);self.assertEqual(data.accounting_csv(),exported)
   expected=json.loads((ROOT/'offhost-first-results.json').read_text())['export_sha256'];self.assertEqual(hashlib.sha256(exported).hexdigest(),expected)
   rows=list(csv.DictReader(io.StringIO(exported.decode('utf-8-sig')),delimiter=';'));self.assertTrue({'invoice','payment','sale','sale_payment','sale_return','sale_refund'}<={r['record_type'] for r in rows});self.assertEqual(sum(int(r['cashflow_effect_cents'] or 0) for r in rows),77290)
   # The serializer operates only on an explicit snapshot, without live business state.
   workflow.FILE=Path(tmp)/'nonexistent.json';self.assertEqual(accounting.export_csv(snapshot),exported)
   bad=copy.deepcopy(snapshot);bad['currency']='USD'
   with self.assertRaises(ValueError):accounting.export_csv(bad)
 def test_invoice_credit_receipt_and_refund_stay_linked_in_snapshot(self):
  snapshot=dict(schema_version=1,currency='EUR',documents=[dict(order='W_TEST',customer='TEST fictief',source_sha256='test-source',accounting_state='pending',balance=dict(received_cents=12100,credits_cents=6050,refunded_cents=6050,open_cents=0),invoice=dict(id='F_TEST',status='definitief',issued_date='2026-10-26',due='2026-11-09',net_cents=10000,vat_cents=2100,total_cents=12100,paid_cents=12100,credits=[dict(id='C_TEST',date='2026-10-26',net_cents=5000,vat_cents=1050,total_cents=6050,reason='TEST credit')],payments=[dict(id='P_TEST',date='2026-10-26',cents=12100,method='bank',reference='TEST betaling')],refunds=[dict(id='R_TEST',date='2026-10-26',cents=6050,method='bank',reference='TEST terugbetaling')]))],sales=[])
  rows=list(csv.DictReader(io.StringIO(accounting.export_csv(snapshot).decode('utf-8-sig')),delimiter=';'));self.assertEqual([r['record_type'] for r in rows],['invoice','credit','payment','refund']);self.assertTrue(all(r['original_invoice']=='F_TEST' for r in rows));self.assertEqual(sum(int(r['cashflow_effect_cents'] or 0) for r in rows),6050);self.assertEqual(sum(int(r['net_cents'] or 0) for r in rows if r['record_type'] in {'invoice','credit'}),5000)
if __name__=='__main__':unittest.main(verbosity=2)
