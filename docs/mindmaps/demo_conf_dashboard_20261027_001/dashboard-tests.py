"""Read-model regressions on an isolated copy; never writes live dossiers."""
import copy,json,tempfile
from pathlib import Path
import workflow,business,data
from improvements import payment_attention
checks=[]
with tempfile.TemporaryDirectory() as tmp:
 workflow.FILE=Path(tmp)/'workflow.json';workflow.FILE.write_bytes(Path('live-reference.json').read_bytes())
 def act(action,job='W104',**kw):return workflow.apply(dict(action=action,job=job,role='Eigenaar',revision=workflow.load()['revision'],**kw))
 d=data.dashboard();attention=d['owner']['attention'];assert len({('invoice',a['invoice']) if a.get('invoice') else ('work',a['order']) for a in attention})==len(attention);assert all(a['customer'] and a['responsible'] for a in attention);checks.append('unique attention with customer/responsibility')
 # Payment missing confirmation alone counts once. Reversed payments do not count.
 s=workflow.load();inv=s['jobs']['W106']['sales_invoice'];inv['payments']=[dict(id='TEST-metadata',cents=100,date=data.DAY,method='bank',reference='TEST')]
 assert len([p for p in payment_attention(s) if p['job']=='W106'])==1
 inv['payments'][0]['reversal']={'date':data.DAY};assert not any(p['job']=='W106' for p in payment_attention(s));checks.append('missing source confirmation counted; reversal excluded')
 # Same roster, overlapping blocks, and elapsed time. No reference to the real clock.
 s=workflow.load();s['operations']['work_patterns']['Noor']=dict(days=list(range(7)),start='09:00',end='17:00',source='TEST');s['operations']['timeblocks']={
 'TEST-a':dict(id='TEST-a',employee='Noor',day='2026-11-10',start='10:00',end='11:00',kind='pauze'),
 'TEST-b':dict(id='TEST-b',employee='Noor',day='2026-11-10',start='10:30',end='12:00',kind='afwezig')}
 def capacity(at):return next(a for a in business.availability(s,'2026-11-10',at) if a['employee']=='Noor')
 assert capacity('09:00')['free_minutes']==360 and capacity('09:00')['remaining_minutes']==360
 assert capacity('10:30')['remaining_minutes']==300 and capacity('16:30')['remaining_minutes']==30 and capacity('18:00')['remaining_minutes']==0
 assert capacity('00:00')['free_minutes']==360;checks.append('overlapping blocks and total/remaining capacity at five simulated times')
 s['operations']['work_patterns'].pop('Noor');assert next(a for a in business.availability(s,'2026-11-10') if a['employee']=='Noor')['remaining_minutes'] is None;checks.append('missing roster stays unknown')
 # A follow-up on the fixed demoday is valid even when the host day is later.
 legacy=next(i for i in d['invoices'] if i['id']=='F103');assert legacy['overdue']
 act('invoice_followup',invoice='F103',note='TEST volg op demodag op',next_date=data.DAY,responsible='Administratie');assert data.dashboard()['invoices'][next(n for n,i in enumerate(data.dashboard()['invoices']) if i['id']=='F103')]['followup']['next_date']==data.DAY
 checks.append('overdue and follow-up validation share fixed demoday')
 act('stock_receive',part='TEST vaste dag',location='winkel',quantity=2,source='TEST fictief')
 act('sale',part='TEST vaste dag',location='winkel',quantity=1,unit_cents=1000,source='TEST prijs')
 sale=list(workflow.load()['operations']['sales'].values())[-1];assert sale['date']==data.DAY
 checks.append('automatic sale/event business dates use fixed demoday')
 result=dict(result='PASS',checks=checks);Path('dashboard-results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
