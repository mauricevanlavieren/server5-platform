import copy,csv,io,json,tempfile,uuid
from pathlib import Path
from unittest.mock import patch
import workflow,data,business
from improvements import dossier_state,payment_id,balance
original=Path('live-reference.json').read_bytes()
with tempfile.TemporaryDirectory() as tmp:
 workflow.FILE=Path(tmp)/'state.json';workflow.FILE.write_bytes(original)
 def act(action,job='W104',**kw):return workflow.apply(dict(action=action,job=job,role='Eigenaar',revision=workflow.load()['revision'],**kw))
 def reject(action,job='W104',**kw):
  before=workflow.FILE.read_bytes()
  try:act(action,job,**kw)
  except ValueError:assert workflow.FILE.read_bytes()==before;return
  raise AssertionError('Ongeldig geaccepteerd: '+action)
 # Legacy metadata changes no amount, preserves original blank source and audit.
 ident='W112';act('admin_reopen',ident,reason='TEST metadata historical')
 j=workflow.view()['jobs'][ident];pid=j['sales_invoice']['payments'][0]['id'];prior=copy.deepcopy(workflow.load()['jobs'][ident]['sales_invoice']);value=prior['paid_cents']
 act('payment_metadata',ident,payment=pid,payment_date='2026-10-26',method='bank',reference='TEST aantoonbare bron',source_status='verified',reason='TEST bron gecontroleerd')
 inv=workflow.load()['jobs'][ident]['sales_invoice'];assert inv['paid_cents']==value and inv['total_cents']==prior['total_cents'];assert inv['payments'][0]['metadata_history'][0]['before']==prior['payments'][0]
 assert dossier_state(workflow.load(),ident)['work']=='Opnieuw in behandeling'
 reject('payment_metadata',ident,payment=pid,payment_date='',method='',reference='',source_status='verified',reason='TEST onvoldoende')
 act('payment_metadata',ident,payment=pid,payment_date='',method='',reference='',source_status='unverified',reason='TEST bron blijkt onvoldoende')
 assert dossier_state(workflow.load(),ident)['metadata_unknown']==1
 assert workflow.load()['jobs'][ident]['sales_invoice']['payments'][0]['date'] is None
 unknown_dashboard=data.dashboard();assert sum(unknown_dashboard['owner']['payment_channels'].values())-unknown_dashboard['receipts']['refund_cents']==unknown_dashboard['payments_cents']
 # Requests are replay-safe after intervening revisions, even when the response is lost.
 request_id=uuid.uuid4().hex;payload=dict(action='credit',job=ident,role='Eigenaar',revision=workflow.load()['revision'],net_cents=1001,date='2026-10-26',reason='TEST paid credit',request_id=request_id)
 workflow.apply(payload);first=workflow.FILE.read_bytes();workflow.apply(payload);assert workflow.FILE.read_bytes()==first
 try:workflow.apply(dict(payload,net_cents=2000))
 except ValueError:pass
 else:raise AssertionError('Reused request id accepted different amount')
 assert workflow.FILE.read_bytes()==first
 j=workflow.view()['jobs'][ident];assert j['dossier_flow']['target']=='refund' and j['state']['balance']['open_cents']==-1211
 assert 'terugbetalen' in j['state']['payment']
 act('refund',ident,cents=1211,date='2026-10-26',method='bank',reference='TEST refund',reason='TEST credit')
 act('admin_close',ident);assert workflow.view()['jobs'][ident]['dossier_flow']['target']=='done'
 act('admin_reopen',ident,reason='TEST second reopen');act('payment_reverse',ident,payment=pid,date='2026-10-26',reason='TEST original wrong')
 assert balance(workflow.load()['jobs'][ident]['sales_invoice'])['open_cents']==7260
 act('payment',ident,cents=7260,date='2026-10-26',method='card',reference='TEST corrected')
 # Export relationship and signed-value reconciliation, incl. metadata and unknown date.
 csvdata=data.accounting_csv().decode('utf-8-sig');rows=list(csv.DictReader(io.StringIO(csvdata),delimiter=';'))
 rows=[r for r in rows if r['order']==ident];invoice=next(r for r in rows if r['record_type']=='invoice')
 signed=sum(int(r['total_cents']) for r in rows if r['record_type'] in {'payment','payment_reversal','refund'})
 assert signed==int(invoice['received_cents'])-int(invoice['refund_cents'])
 assert all(r['original_invoice']==invoice['id'] for r in rows)
 assert len({r['id'] for r in rows})==len(rows)
 assert any(r['record_type']=='payment_metadata' and r['parent_payment']==pid for r in rows)
 assert any(r['record_type']=='payment' and r['missing_fields']=='date|method|reference' and r['date']=='UNKNOWN' for r in rows)
 assert all(r['required_mappings'] for r in rows)
 # Actual storage failure leaves prior bytes; retry same id stores one credit.
 before=workflow.FILE.read_bytes();request_id=uuid.uuid4().hex
 with patch('workflow.os.replace',side_effect=OSError('TEST disk error')):
  try:act('credit',ident,net_cents=100,date='2026-10-26',reason='TEST retry',request_id=request_id)
  except OSError:pass
  else:raise AssertionError('Disk error swallowed')
 assert workflow.FILE.read_bytes()==before
 payload=dict(action='credit',job=ident,role='Eigenaar',revision=workflow.load()['revision'],net_cents=100,date='2026-10-26',reason='TEST retry',request_id=request_id)
 workflow.apply(payload);saved=workflow.FILE.read_bytes();workflow.apply(payload);assert workflow.FILE.read_bytes()==saved
 # Canonical label is shared by dashboard and dossier; regressions preserve every stored byte.
 s=workflow.load();d=data.dashboard();v=workflow.view()
 assert next(r for r in d['owner']['records'] if r['id']==ident)['status']==v['jobs'][ident]['status']
 initial=json.loads(original)
 for key in ['W106','W109']:assert s['jobs'][key]==initial['jobs'][key]
 # A blocked delivery must drive the guide and prevent premature completion.
 act('intake',customer='TEST status levering',contact='TEST',scope='TEST onderdeel',priority='normaal',address='Teststraat 3',phone='000',access='TEST')
 gid=list(workflow.load()['operations']['orders'])[-1]
 act('direct_agreement',gid,who='TEST klant',date='2026-10-26',reference='TEST akkoord')
 act('plan',order=gid,appointment='2026-10-26T08:00',employee='Bram',duration_minutes=60)
 act('waiting_part',order=gid,part='TEST levering status',supplier='TEST leverancier',responsible='Lina',followup_date='2026-10-26',expected_delivery='2026-10-26')
 assert workflow.view()['jobs'][gid]['dossier_flow']['target']=='part_purchase'
 reject('finish',gid,findings='TEST nog niet klaar',hours=1,materials='Geen materiaal',visit_hours={'diagnosis':1})
 act('part_purchase',order=gid,quantity=2,location='winkel')
 assert workflow.view()['jobs'][gid]['dossier_flow']['target']=='part_ordered'
 act('part_ordered',order=gid)
 pid=workflow.load()['jobs'][gid]['waiting_part']['purchase_id']
 act('purchase_partial',purchase=pid,quantity=1)
 assert workflow.view()['jobs'][gid]['dossier_flow']['target']=='purchase_partial'
 reject('finish',gid,findings='TEST nog niet klaar',hours=1,materials='Geen materiaal',visit_hours={'diagnosis':1})
 act('part_receive',order=gid)
 assert workflow.view()['jobs'][gid]['dossier_flow']['target']=='followup_plan'
 act('followup_plan',order=gid,appointment='2026-10-26T12:00',employee='Bram',duration_minutes=60)
 assert workflow.view()['jobs'][gid]['dossier_flow']['target']=='execution'
 print(json.dumps(dict(result='PASS',checks=['legacy metadata preserves amounts and originals','unknown sources explicit','reopened status consistent','credit selects refund','refund then close','reverse then correct after refund','request replay after response loss','storage failure and safe retry','export signs/links/mappings/missing fields','W106/W109 exact state retained','parts guide and premature finish guards']),ensure_ascii=False,indent=2))
