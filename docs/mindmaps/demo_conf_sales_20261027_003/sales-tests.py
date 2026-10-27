from pathlib import Path
import copy,json,tempfile,uuid,csv,io
import workflow,data,business
original=Path('live-reference.json').read_bytes();checks=[]
with tempfile.TemporaryDirectory() as tmp:
 workflow.FILE=Path(tmp)/'state.json';workflow.FILE.write_bytes(original)
 def act(a,job='W104',role='Eigenaar',**kw):return workflow.apply(dict(action=a,job=job,role=role,revision=workflow.load()['revision'],**kw))
 def reject(a,**kw):
  before=workflow.FILE.read_bytes()
  try:act(a,**kw)
  except ValueError:assert workflow.FILE.read_bytes()==before;return
  raise AssertionError('Invalid accepted '+a)
 d=data.dashboard();assert d['payments_cents']==77290;st=workflow.load();assert st['operations']['purchases']['I2']['received_quantity']==4 and st['operations']['sales']['B2']['returns'][0]['total_cents']==1210 and st['jobs']['W113']['sales_invoice']['total_cents']==9680;checks.append('I2/B2/W113 and 77290 net practice regressions preserved')
 def newjob():
  act('intake',customer='TEST VERKOOP route',contact='TEST',scope='TEST materiaal',priority='normaal',address='Teststraat',phone='000',access='TEST');return list(workflow.load()['operations']['orders'])[-1]
 job=newjob();act('stock_receive',part='TEST gedeeltelijk',location='winkel',quantity=5,source='TEST');act('reserve',order=job,part='TEST gedeeltelijk',location='winkel',quantity=3,unit_cents=1000,price_source='TEST');rid=list(workflow.load()['operations']['reservations'])[-1]
 act('reservation_release',job,reservation=rid,quantity=1,reason='TEST één vrij');r=workflow.load()['operations']['reservations'][rid];assert r['quantity']==2 and r['status']=='gereserveerd' and r['original_quantity']==3
 reject('reservation_release',job=job,reservation=rid,quantity=3,reason='TEST te veel');act('stock_use',job,reservation=rid)
 act('direct_agreement',job,who='TEST',date=data.DAY,reference='TEST');act('plan',order=job,employee='Noor',appointment='2026-11-03T09:00',duration_minutes=60)
 act('finish',job,role='Bram',findings='TEST gereed',hours=1,materials='');act('invoice_draft',job,role='Administratie',rate_cents=6000,source='TEST',due='2026-11-09')
 assert workflow.load()['jobs'][job]['sales_invoice']['net_cents']==8000
 request=dict(action='material_return',job=job,role='Eigenaar',revision=workflow.load()['revision'],reservation=rid,quantity=1,reason='TEST één retour',request_id=uuid.uuid4().hex);workflow.apply(request);workflow.apply(request)
 assert workflow.load()['operations']['stock']['TEST gedeeltelijk @ winkel']==4 and workflow.load()['jobs'][job]['sales_invoice']['net_cents']==7000
 reject('material_return',job=job,reservation=rid,quantity=2,reason='TEST te veel')
 act('invoice_final',job,role='Administratie',confirmed=True);inv=copy.deepcopy(workflow.load()['jobs'][job]['sales_invoice']);assert inv['issued_date']==data.DAY
 reject('material_return',job=job,reservation=rid,quantity=1,reason='TEST zonder credit')
 act('credit',job,net_cents=1000,date=data.DAY,reason='TEST retour');credit=workflow.load()['jobs'][job]['sales_invoice']['credits'][-1]['id'];act('material_return',job,reservation=rid,quantity=1,reason='TEST definitieve retour',credit_id=credit)
 assert workflow.load()['jobs'][job]['sales_invoice']['lines']==inv['lines'] and workflow.load()['operations']['stock']['TEST gedeeltelijk @ winkel']==5
 assert not business.invoice_control(workflow.view(),job)['blocked'];reject('material_return',job=job,reservation=rid,quantity=1,reason='TEST dubbel',credit_id=credit)
 checks.append('partial release, partial concept return, credited final return; bounds, replay, immutable final invoice, stock and invoice controls')
 # Second partial final return exercises remaining consumed material.
 job2=newjob();act('reserve',order=job2,part='TEST gedeeltelijk',location='winkel',quantity=2,unit_cents=1000,price_source='TEST');r2=list(workflow.load()['operations']['reservations'])[-1];act('stock_use',job2,reservation=r2)
 act('direct_agreement',job2,who='TEST',date=data.DAY,reference='TEST');act('plan',order=job2,employee='Noor',appointment='2026-11-03T10:00',duration_minutes=60);act('finish',job2,role='Bram',findings='TEST',hours=1,materials='');act('invoice_draft',job2,role='Administratie',rate_cents=6000,source='TEST',due='2026-11-09');act('invoice_final',job2,role='Administratie',confirmed=True);act('credit',job2,net_cents=1000,date=data.DAY,reason='TEST');cid=workflow.load()['jobs'][job2]['sales_invoice']['credits'][0]['id'];act('material_return',job2,reservation=r2,quantity=1,reason='TEST',credit_id=cid);assert not business.invoice_control(workflow.view(),job2)['blocked'];reject('material_return',job=job2,reservation=r2,quantity=1,reason='TEST te lage credit',credit_id=cid);checks.append('partial final return matches credited quantity without blocking valid invoice control')
 act('invoice_date','W101',invoice='F101',date='2026-10-20',source='TEST aantoonbaar archiefstuk');j=workflow.load()['jobs']['W101'];assert j['sales_invoice']['date_history'][0]['before'] is None
 reject('invoice_date',job='W101',invoice='F101',date='2026-10-19',source='TEST overschrijf');reject('invoice_date',job='W103',date='2026-10-27',source='TEST toekomst');checks.append('new issue dates and historical date fill with source/history; no known-date overwrite')
 before=copy.deepcopy(workflow.load());req=dict(action='tour_prepare',job='W104',role='Eigenaar',revision=before['revision'],request_id=uuid.uuid4().hex);workflow.apply(req);workflow.apply(req);act('tour_prepare');s=workflow.load();assert len(s['operations']['demo_runs'])==2
 for k,j in before['jobs'].items():assert s['jobs'][k]==j
 for k,v in before['operations']['stock'].items():assert s['operations']['stock'][k]==v
 assert s['history'][:len(before['history'])]==before['history'];checks.append('new tour rounds append only; retries do not duplicate; prior jobs/stock/history retained')
 rows=list(csv.DictReader(io.StringIO(data.accounting_csv().decode('utf-8-sig')),delimiter=';'));assert sum(int(r['cashflow_effect_cents']) for r in rows)==data.dashboard()['payments_cents'];assert any(r['record_type']=='invoice_date_metadata' for r in rows);checks.append('financial export and date evidence reconcile')
Path('sales-results.json').write_text(json.dumps(dict(result='PASS',checks=checks),indent=2));print(json.dumps(dict(result='PASS',checks=checks),indent=2))
