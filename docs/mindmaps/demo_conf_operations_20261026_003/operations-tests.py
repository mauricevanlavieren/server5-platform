import json,copy,tempfile,uuid
from pathlib import Path
import workflow,business,data
from improvements import payment_attention,balance
original=Path('live-reference.json').read_bytes()
with tempfile.TemporaryDirectory() as tmp:
 workflow.FILE=Path(tmp)/'state.json';workflow.FILE.write_bytes(original)
 def act(action,job='W104',**kw):return workflow.apply(dict(action=action,job=job,role='Eigenaar',revision=workflow.load()['revision'],**kw))
 def reject(action,job='W104',**kw):
  before=workflow.FILE.read_bytes()
  try:act(action,job,**kw)
  except ValueError:assert workflow.FILE.read_bytes()==before;return
  raise AssertionError('Invalid accepted '+action)
 # Only active missing metadata counts. Correcting a closed dossier changes no money.
 st=workflow.view()['jobs']['W106']['state'];assert st['metadata_unknown']==1 and st['historical_metadata_unknown']==1
 s=workflow.load();inv=copy.deepcopy(s['jobs']['W106']['sales_invoice']);issue=next(i for i in data.dashboard()['payment_attention'] if i['job']=='W106')
 act('payment_metadata','W106',payment=issue['payment_id'],payment_date='2026-10-26',method='bank',reference='TEST bron voor ontbrekende methode',source_status='verified',reason='TEST uitsluitend brongegevens')
 st=workflow.view()['jobs']['W106']['state'];after=workflow.load()['jobs']['W106'];assert st['metadata_unknown']==0 and st['historical_metadata_unknown']==1 and after['administrative_closed']
 assert balance(after['sales_invoice'])==balance(inv) and after['sales_invoice']['payments'][0]==inv['payments'][0]
 assert not any(i['job']=='W106' for i in data.dashboard()['payment_attention'])
 d=data.dashboard();assert sum(i['cents'] for i in d['payment_attention'] if not i['method'])==d['owner']['payment_channels']['unspecified']
 # Unknown, recurring, day off, day override, pause, absence, travel, completed visit.
 def available(employee,day):return next(x for x in business.availability(workflow.load(),day) if x['employee']==employee)
 assert not available('Noor','2026-11-03')['availability_known'] and available('Noor','2026-11-03')['free_minutes'] is None
 act('work_pattern',employee='Noor',days=[0,1,2,3,4],start='09:00',end='17:00',source='TEST fictief weekrooster')
 assert available('Noor','2026-11-03')['free_minutes']==480
 assert available('Noor','2026-11-01')['free_minutes']==0 and available('Noor','2026-11-01')['availability_known']
 assert not available('Lina','2026-11-03')['availability_known']
 act('worktime',employee='Noor',day='2026-11-03',start='10:00',end='16:00')
 act('timeblock',employee='Noor',day='2026-11-03',kind='pauze',start='12:00',end='12:30')
 act('timeblock',employee='Noor',day='2026-11-03',kind='afwezig',start='13:00',end='14:00')
 act('intake',customer='TEST teamcapaciteit',contact='TEST',scope='TEST planbaar werk',priority='normaal',address='Teststraat 1',phone='000',access='TEST')
 job=list(workflow.load()['operations']['orders'])[-1];act('direct_agreement',job,who='TEST klant',date='2026-10-26',reference='TEST akkoord')
 act('plan',order=job,employee='Noor',appointment='2026-11-03T15:00',duration_minutes=60)
 act('timeblock',order=job,employee='Noor',day='2026-11-03',kind='reistijd',start='14:30',end='15:00')
 assert available('Noor','2026-11-03')['free_minutes']==180
 workflow.apply(dict(action='finish',job=job,role='Bram',revision=workflow.load()['revision'],findings='TEST klaar',hours=1,materials='Geen materiaal'))
 assert available('Noor','2026-11-03')['free_minutes']==180 and len(available('Noor','2026-11-03')['history'])==1
 reject('plan',order='W109',employee='Noor',appointment='2026-11-03T15:00',duration_minutes=60)
 # Stock reservation/free/release/use/return and identical-request replay.
 act('intake',customer='TEST voorraadroute',contact='TEST',scope='TEST materiaal',priority='normaal',address='Teststraat 2',phone='000',access='TEST')
 matjob=list(workflow.load()['operations']['orders'])[-1]
 act('stock_receive',part='TEST route',location='winkel',quantity=5,source='TEST beginvoorraad')
 act('reserve',order=matjob,part='TEST route',location='winkel',quantity=2,unit_cents=1000,price_source='TEST prijs')
 rid=list(workflow.load()['operations']['reservations'])[-1];stock=next(i for i in data.dashboard()['owner']['stock'] if i['key']=='TEST route @ winkel');assert stock['quantity']==5 and stock['free']==3
 act('reservation_release',matjob,reservation=rid,reason='TEST niet nodig');reject('reservation_release',matjob,reservation=rid,reason='TEST dubbel')
 act('reserve',order=matjob,part='TEST route',location='winkel',quantity=1,unit_cents=1000,price_source='TEST prijs')
 rid=list(workflow.load()['operations']['reservations'])[-1]
 req=dict(action='stock_use',role='Bram',job=matjob,reservation=rid,revision=workflow.load()['revision'],request_id=uuid.uuid4().hex)
 workflow.apply(req);workflow.apply(req);assert workflow.load()['operations']['stock']['TEST route @ winkel']==4
 act('material_return',matjob,reservation=rid,reason='TEST ongebruikt retour');assert workflow.load()['operations']['stock']['TEST route @ winkel']==5
 reject('material_return',matjob,reservation=rid,reason='TEST dubbel')
 # Archived payments retain actionable source corrections even during a replacement concept.
 act('admin_reopen','W112',reason='TEST archiefbron')
 act('credit','W112',net_cents=6000,date='2026-10-26',reason='TEST geheel crediteren')
 act('refund','W112',cents=7260,date='2026-10-26',method='bank',reference='TEST refund',reason='TEST credit')
 act('invoice_replace','W112',net_cents=5000,due='2026-11-10',reason='TEST vervanging')
 archived=workflow.view()['jobs']['W112']['invoice_archive'][0];pid=archived['payments'][0]['id']
 act('payment_metadata','W112',payment=pid,payment_date='2026-10-26',method='bank',reference='TEST archiefbron aangetoond',source_status='verified',reason='TEST bronbewijs')
 j=workflow.view()['jobs']['W112'];assert j['state']['metadata_unknown']==0 and j['sales_invoice']['status']=='concept' and j['invoice_archive'][0]['paid_cents']==7260
 assert workflow.load()['jobs']['W109']==json.loads(original)['jobs']['W109']
 print(json.dumps(dict(result='PASS',checks=['active vs reversed metadata warnings','closed metadata fix preserves all amounts and closure','dashboard unknown-method total equals active records','unknown is not free','recurring weekday and explicit day off','day override and all busy blocks','completed visit in history and capacity','reservation/free/release/use/return','persistent duplicate request protection','W109 unchanged','metadata route for archived payment during replacement concept']),ensure_ascii=False,indent=2))
