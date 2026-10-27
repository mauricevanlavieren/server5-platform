"""Priority and cash reconciliation regressions; all writes use a temporary fixture."""
from pathlib import Path
import copy,csv,io,json,tempfile
import workflow,data
checks=[]
with tempfile.TemporaryDirectory() as tmp:
 workflow.FILE=Path(tmp)/'workflow.json';workflow.FILE.write_bytes(Path('live-reference.json').read_bytes())
 def act(action,job='W104',role='Eigenaar',**kw):return workflow.apply(dict(action=action,job=job,role=role,revision=workflow.load()['revision'],**kw))
 def reject(action,**kw):
  before=workflow.FILE.read_bytes()
  try:act(action,**kw)
  except ValueError:assert workflow.FILE.read_bytes()==before;return
  raise AssertionError('Unexpected success '+action)
 def reconcile():
  before=workflow.FILE.read_bytes();d=data.dashboard();rows=list(csv.DictReader(io.StringIO(data.accounting_csv().decode('utf-8-sig')),delimiter=';'));types={'payment','payment_reversal','refund','sale_payment','sale_refund'}
  assert sum(int(r['cashflow_effect_cents']) for r in rows)==d['payments_cents']
  assert sum(int(r['net_received_cents']) for r in rows if r['record_type'] in {'invoice','sale'})==d['payments_cents']
  assert sum(int(r['total_cents']) for r in rows if r['record_type'] in types)==d['payments_cents']==d['receipts']['net_cents']
  assert sum(d['receipts']['channels'].values())-d['receipts']['refund_cents']==d['payments_cents'];assert workflow.FILE.read_bytes()==before
  for channel in ['bank','cash','card','unspecified']:
   expected=sum(p['cents'] for p in d['payments'] if p['channel']==channel and p['kind'] not in {'refund','sale_refund'})
   assert d['receipts']['channels'][channel]==expected
  return d
 d=reconcile();assert d['payments_cents']==76080;assert d['receipts']['gross_cents']==79105;assert d['receipts']['refund_cents']==3025;assert d['receipts']['reversal_cents']==5000
 checks.append('original 76080 net = 44040 bank + 605 cash + 0 card + 34460 unknown - 3025 refunds; 5000 reversal not double counted')
 assert sum(a.get('action')=='work_pattern' and a.get('employee')=='Lina' for a in d['owner']['attention'])==1
 act('work_pattern',employee='Lina',days=[0,1,2,3,4],start='09:00',end='17:00',source='TEST fictief rooster');d=reconcile();assert not any(a.get('action')=='work_pattern' and a.get('employee')=='Lina' for a in d['owner']['attention']);assert next(a for a in d['owner']['availability'] if a['employee']=='Lina')['availability_known'];checks.append('roster task disappears and capacity recalculates')
 invbefore=copy.deepcopy(workflow.load()['jobs']['W107']['sales_invoice']);act('invoice_rule',days=2,source='TEST interne actietermijn');act('completion_date','W107',date='2026-10-21',source='TEST bewijs gereedmelding');d=reconcile();a=next(a for a in d['owner']['attention'] if a['order']=='W107');assert a['waiting_days']==5 and a['deadline']=='2026-10-23' and a['priority_group']=='vervallen' and a['amount_cents']==10000
 assert workflow.load()['jobs']['W107']['sales_invoice']==invbefore;assert len(workflow.load()['jobs']['W107']['completion_date_history'])==1
 reject('invoice_rule',days=-1,source='TEST');reject('invoice_rule',days=True,source='TEST');reject('completion_date',job='W107',date='2026-10-27',source='TEST');checks.append('explicit invoice rule + audited completion correction; future date and invalid rules rejected; invoice unchanged')
 # No date history is fabricated for a completed legacy item lacking evidence.
 s=workflow.load();s['jobs']['W107'].pop('completed_date');s['history']=[h for h in s['history'] if not(h.get('job')=='W107' and h.get('action') in {'finish','handoff','register'})];workflow.FILE.write_text(json.dumps(s));a=next(a for a in data.dashboard()['owner']['attention'] if a['order']=='W107');assert a['completed_date'] is None and a['waiting_days'] is None and a['deadline'] is None;checks.append('unknown completion date does not fabricate age or deadline')
 # Refunds per channel and exact inverse of corrected/reversed source.
 s=workflow.load();inv=s['jobs']['W106']['sales_invoice'];inv['payments'][1]['method']='card';inv['refunds'][0]['method']='card';workflow.FILE.write_text(json.dumps(s));d=reconcile();assert d['receipts']['channels']['card']==10125 and d['receipts']['refund_cents']==3025;checks.append('card and refunds reconcile independently with the signed export')
 act('intake',customer='TEST spoedprioriteit',contact='TEST',scope='TEST urgente route',priority='spoed',address='Teststraat',phone='000',access='TEST')
 urgent=list(workflow.load()['operations']['orders'])[-1]
 act('intake',customer='TEST blokkeerprioriteit',contact='TEST',scope='TEST ontbrekend onderdeel',priority='normaal',address='Teststraat',phone='000',access='TEST')
 blocked=list(workflow.load()['operations']['orders'])[-1]
 act('waiting_part',order=blocked,part='TEST prioriteitonderdeel',supplier='TEST leverancier',responsible='Lina',followup_date='2026-10-28',expected_delivery='2026-10-29')
 attention=data.dashboard()['owner']['attention'];ranking={'spoed':0,'vervallen':1,'geblokkeerd':2,'administratie':3,'inrichting':4};ranks=[ranking[a['priority_group']] for a in attention]
 assert ranks==sorted(ranks) and attention[0]['order']==urgent and next(a for a in attention if a['order']==blocked)['priority_group']=='geblokkeerd'
 assert len({('invoice',a['invoice']) if a.get('invoice') else ('work',a['order']) for a in attention})==len(attention);checks.append('urgent then overdue then blocked then administration then setup; duplicate work actions collapsed')
 reject('invoice_rule',role='Bram',days=2,source='TEST');checks.append('configuration role guard')
 import answers
 assert data.money(data.dashboard()['receipts']['net_cents']) in answers.answer('Wat is netto ontvangen?')['answer'];assert 'methode onbekend' in answers.answer('betalingen')['answer'];checks.append('demo finance answers use current cashflow and definition')
Path('daily-results.json').write_text(json.dumps(dict(result='PASS',checks=checks),indent=2));print(json.dumps(dict(result='PASS',checks=checks),indent=2))
