import workflow,data,business,json,tempfile,copy
from pathlib import Path
from improvements import balance
before=Path('live-reference.json').read_bytes()
with tempfile.TemporaryDirectory() as tmp:
 workflow.FILE=Path(tmp)/'workflow.json';workflow.FILE.write_bytes(before)
 def act(a,job='W113',role='Eigenaar',**kw):return workflow.apply(dict(action=a,job=job,role=role,revision=workflow.load()['revision'],**kw))
 def reject(a,**kw):
  old=workflow.FILE.read_bytes()
  try:act(a,**kw)
  except ValueError:
   assert workflow.FILE.read_bytes()==old
   return
  raise AssertionError('Accepted invalid '+a)
 act('intake',job='W104',customer='TEST Demo-conf (fictief)',contact='Fictieve contactpersoon',scope='TEST reparatie',priority='normaal',address='Teststraat 1',phone='0000000000',access='Test')
 job=list(workflow.load()['operations']['orders'])[-1]
 def actjob(a,**kw):return act(a,job=job,**kw)
 actjob('direct_agreement',who='TEST klant',date='2026-10-26',reference='TEST direct akkoord')
 actjob('plan',order=job,appointment='2026-10-26T08:00',employee='Bram',duration_minutes=60)
 actjob('finish',role='Bram',findings='TEST reparatie gereed',hours=1.25,materials='Geen materiaal')
 actjob('invoice_draft',rate_cents=6000,source='TEST standaard',due='2026-10-25')
 actjob('invoice_final',confirmed=True);actjob('invoice_send')
 actjob('payment',cents=3000,date='2026-10-26',method='bank',reference='TEST deelbetaling')
 inv=workflow.load()['jobs'][job]['sales_invoice'];assert balance(inv)['open_cents']==6075
 reject('payment',job=job,cents=999999,date='2026-10-26',method='bank',reference='TEST overpayment');reject('payment',job=job,cents=1,date='bad',method='bank',reference='TEST invalid date')
 pid=inv['payments'][0]['id'];actjob('payment_reverse',payment=pid,reason='TEST fout',date='2026-10-26')
 assert balance(workflow.load()['jobs'][job]['sales_invoice'])['open_cents']==9075
 reject('payment_reverse',job=job,payment=pid,reason='TEST duplicate',date='2026-10-26')
 actjob('credit',net_cents=1001,reason='TEST gedeeltelijke credit',date='2026-10-26')
 inv=workflow.load()['jobs'][job]['sales_invoice'];assert inv['credits'][0]['vat_cents']==210 and balance(inv)['open_cents']==7864
 actjob('payment',cents=7864,date='2026-10-26',method='card',reference='TEST restant')
 actjob('admin_close');reject('credit',job=job,net_cents=1,reason='TEST closed',date='2026-10-26');actjob('admin_reopen',reason='TEST correctie na afsluiting')
 actjob('credit',net_cents=6499,reason='TEST restant credit',date='2026-10-26')
 inv=workflow.load()['jobs'][job]['sales_invoice'];assert sum(c['vat_cents'] for c in inv['credits'])==1575
 actjob('refund',cents=7864,date='2026-10-26',method='bank',reference='TEST terugbetaling',reason='TEST tegoed')
 actjob('invoice_replace',net_cents=5000,due='2026-11-01',reason='TEST vervanging')
 actjob('invoice_final',confirmed=True);actjob('invoice_send')
 d=data.dashboard();assert sum(i['open_cents'] for i in d['invoices'] if i['order']==job)==6050
 assert sum(i['net_cents']-i.get('credit_net_cents',0) for i in d['invoices'] if i['order']==job)==5000
 # Stale revision rejects a replay, including a second click.
 prior=workflow.FILE.read_bytes()
 try:workflow.apply(dict(action='payment',job=job,role='Eigenaar',revision=workflow.load()['revision']-1,cents=1,date='2026-10-26',method='bank',reference='TEST replay'))
 except ValueError:pass
 else:raise AssertionError('Stale revision accepted')
 assert workflow.FILE.read_bytes()==prior
 # Historical F103 corrections do not duplicate invoice/receipt.
 act('payment',job='W103',cents=100,date='2026-10-26',method='bank',reference='TEST F103')
 d=data.dashboard();assert len([i for i in d['invoices'] if i['id']=='F103'])==1
 # Regression protected, same financial contents.
 s=workflow.load();original=json.loads(before)
 for key in ['W106','W112']:assert s['jobs'][key]==original['jobs'][key]
 # Repeat credit VAT on fractional cents closes exactly.
 assert s['jobs'][job]['invoice_archive'][0]['net_cents']==7500
 # Generic export includes corrections and source hashes; downloading cannot mark processing.
 export=data.accounting_csv().decode('utf-8-sig');assert 'payment_reversal' in export and 'credit;' in export and 'refund;' in export and 'source_sha256' in export
 assert not workflow.load()['jobs'][job].get('accounting')
 # New direct agreement, unused reservations, return, cancellation and purchase replay guards.
 act('intake',job='W104',customer='TEST guards (fictief)',contact='TEST',scope='TEST guards',priority='normaal',address='Teststraat 2',phone='000',access='TEST')
 guarded=list(workflow.load()['operations']['orders'])[-1]
 reject('plan',order=guarded,appointment='2026-10-26T10:00',employee='Bram',duration_minutes=60)
 reject('finish',job=guarded,role='Bram',findings='TEST',hours=1,materials='Geen materiaal')
 act('stock_receive',part='TEST guards',location='winkel',quantity=3,source='TEST stock')
 act('reserve',order=guarded,part='TEST guards',location='winkel',quantity=2,unit_cents=1000,price_source='TEST prijs')
 rid=list(workflow.load()['operations']['reservations'])[-1]
 act('reservation_release',job=guarded,reservation=rid,reason='TEST unused')
 reject('reservation_release',job=guarded,reservation=rid,reason='TEST duplicate')
 act('reserve',order=guarded,part='TEST guards',location='winkel',quantity=2,unit_cents=1000,price_source='TEST prijs')
 rid=list(workflow.load()['operations']['reservations'])[-1]
 act('stock_use',reservation=rid)
 act('material_return',job=guarded,reservation=rid,reason='TEST return')
 reject('material_return',job=guarded,reservation=rid,reason='TEST duplicate')
 assert workflow.load()['operations']['stock']['TEST guards @ winkel']==3
 act('order_cancel',job=guarded,reason='TEST cancelled')
 reject('finish',job=guarded,role='Bram',findings='TEST',hours=1,materials='Geen materiaal')
 act('purchase',part='TEST partial',location='winkel',quantity=2,supplier='TEST leverancier')
 pid=list(workflow.load()['operations']['purchases'])[-1]
 act('purchase_partial',purchase=pid,quantity=1)
 act('purchase_receive',purchase=pid)
 reject('purchase_receive',purchase=pid)
 assert workflow.load()['operations']['stock']['TEST partial @ winkel']==2
 act('warranty',order='W112',proof='TEST fictieve garantie',findings='TEST beoordeling')
 claim=workflow.load()['operations']['events'][-1]['id']
 act('warranty_decide',claim=claim,decision='toegekend',findings='TEST garantie erkend')
 print(json.dumps(dict(result='PASS',checks=['payments and reversals','partial credit VAT','cumulative full-credit VAT','refund','replacement and no double ledger','close/reopen','historical F103 deduplication','W106/W112 unchanged','direct agreement/planning guards','release and return idempotency','cancellation and warranty','partial receiving and replay protection']),indent=2))
