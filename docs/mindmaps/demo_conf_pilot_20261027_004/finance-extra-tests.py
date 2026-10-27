import tempfile,json,copy
from pathlib import Path
import workflow,data
checks=[]
with tempfile.TemporaryDirectory() as tmp:
 workflow.FILE=Path(tmp)/'state.json';workflow.FILE.write_bytes(Path('live-reference.json').read_bytes())
 def act(a,job='W104',**kw):return workflow.apply(dict(action=a,job=job,role='Eigenaar',revision=workflow.load()['revision'],**kw))
 def reject(a,**kw):
  before=workflow.FILE.read_bytes()
  try:act(a,**kw)
  except ValueError:assert workflow.FILE.read_bytes()==before;return
  raise AssertionError('Invalid accepted')
 def quote():
  act('quote_new',customer='TEST Meerwerk',contact='TEST',scope='TEST',priority='normaal');job=list(workflow.load()['operations']['orders'])[-1];act('quote_save',job,scope='TEST',source='TEST',net_cents=10000);act('quote_accept',job,confirmed=True,agreement='TEST akkoord');return job
 j=quote();base=dict(approval_who='TEST klant',approval_date=data.DAY,approval_reference='TEST-BASIS',reason='TEST apart geaccordeerd')
 reject('billing_save',job=j,mode='extra',extra_cents=2000,**base)
 act('billing_save',j,mode='extra',extra_cents=2000,extra_who='TEST klant',extra_date=data.DAY,extra_reference='TEST-MEERWERK',extra_description='TEST aanvullende sleutel',**base)
 act('plan',order=j,employee='Noor',appointment='2026-11-03T09:00',duration_minutes=60);workflow.apply(dict(action='finish',job=j,role='Bram',revision=workflow.load()['revision'],findings='TEST',hours=1,materials='Geen materiaal'))
 act('invoice_draft',j,due='2026-11-09');inv=workflow.load()['jobs'][j]['sales_invoice'];assert inv['net_cents']==12000 and inv['total_cents']==14520 and len(inv['lines'])==2 and inv['lines'][1]['net_cents']==2000
 act('invoice_final',j,confirmed=True);original=copy.deepcopy(workflow.load()['jobs'][j]['sales_invoice']);reject('billing_save',job=j,mode='fixed',**base);assert workflow.load()['jobs'][j]['sales_invoice']==original;checks.append('separate extra approval required; quote100 + extra20 = net120/VAT25.20; final agreement immutable')
 j=quote();act('billing_save',j,mode='actual',**base);act('plan',order=j,employee='Noor',appointment='2026-11-03T10:00',duration_minutes=90);workflow.apply(dict(action='finish',job=j,role='Bram',revision=workflow.load()['revision'],findings='TEST',hours=1.5,materials='Geen materiaal'));act('invoice_draft',j,rate_cents=6000,source='TEST afgesproken tarief',due='2026-11-09');inv=workflow.load()['jobs'][j]['sales_invoice'];assert inv['net_cents']==9000 and inv['total_cents']==10890;act('billing_save',j,mode='actual',**{**base,'reason':'TEST actuele afwijking90tegen100 beoordeeld'});act('invoice_final',j,confirmed=True);checks.append('explicit actual-cost agreement: quoted100 differs from 1.5h*60=90, source and approval retained')
Path('finance-extra-results.json').write_text(json.dumps(dict(result='PASS',checks=checks),indent=2));print('PASS approved extra and explicit actual-cost billing')
