"""One consistent fictional ledger; integer cents, fixed demonstration date."""
DAY='2026-10-26'
STAFF=['Noor','Bram','Lina']
TILES=['revenue','payments','invoices','today','stock','followup','actions']
ORDERS=[
 dict(id='W101',customer='De Linde (fictief)',job='Voordeurcilinder vervangen',employee='Bram',time='09:00',cents=24000,status='afgerond'),
 dict(id='W102',customer='Bakkerij Morgen (fictief)',job='Drie sleutels bijmaken',employee='Noor',time='10:00',cents=7500,status='afgerond'),
 dict(id='W103',customer='Studio West (fictief)',job='Deurdranger herstellen',employee='Lina',time='11:00',cents=18000,status='afgerond'),
 dict(id='W104',customer='Familie Vos (fictief)',job='Slot repareren',employee='Bram',time='14:00',cents=9500,status='gepland'),
 dict(id='W105',customer='Atelier Noord (fictief)',job='Veiligheidscilinder plaatsen',employee='Bram',time='16:00',cents=24000,status='wacht op onderdeel'),
 dict(id='W106',customer='Kantoor Kade (fictief)',job='Offerte sluitplan opvolgen',employee='Lina',time='15:00',cents=0,status='opvolgen')]
INVOICES=[dict(id='F101',order='W101',net_cents=24000,vat_cents=5040,due='2026-10-26',paid_cents=29040),dict(id='F102',order='W102',net_cents=7500,vat_cents=1575,due='2026-10-30',paid_cents=0),dict(id='F103',order='W103',net_cents=18000,vat_cents=3780,due='2026-10-23',paid_cents=10000)]
PAYMENTS=[dict(id='B101',invoice='F101',cents=29040,date=DAY),dict(id='B102',invoice='F103',cents=10000,date=DAY)]
STOCK=[dict(id='S01',order='W105',part='Veiligheidscilinder SKG*** 30/35 mm, nikkel, 3 sleutels',supplier='Demo Sluittechniek BV (fictief)',available=0,required=1,delivery='Verwacht 27 oktober, 10:00 — onbevestigd',employee='Lina',installer='Bram',message='Beste Atelier Noord, voor uw afspraak ontbreekt de SKG*** cilinder 30/35 mm. Wij verwachten levering op 27 oktober om 10:00, onder voorbehoud. Na bevestiging stellen wij een nieuwe afspraak voor. Met vriendelijke groet, Sleutelhuis Demo.')]
FOLLOWUP=[dict(id='C01',order='W105',employee='Lina',text='Levering verifiëren en conceptbericht beoordelen; afspraak nog niet bevestigen.'),dict(id='C02',order='W106',employee='Lina',text='Kantoor Kade bellen over conceptofferte sluitplan; nog niet uitgevoerd.')]
ACTIONS=[dict(id='A01',order='W105',status='voorstel',text='Vraag Lina om levering te verifiëren; laat Bram daarna herplannen. Niet uitgevoerd.'),dict(id='A02',order='W103',status='voorstel',text='Controleer verlopen restsaldo F103 van € 117,80; concept herinnering beoordelen. Niet uitgevoerd.')]
STORY=[
 dict(title='1 · Klantvraag',text='Atelier Noord vraagt een veiliger achterdeurcilinder. W105, Bram, 26 oktober 16:00. Nog geen omzet of betaling.'),
 dict(title='2 · Planning & tekort',text='W105 wacht op onderdeel: SKG*** 30/35 mm, nikkel, 3 sleutels. Voorraad 0, nodig 1. Lina controleert Demo Sluittechniek BV; verwacht 27 oktober 10:00, onbevestigd.'),
 dict(title='3 · Conceptklantbericht',text=STOCK[0]['message']+' CONCEPT — niet verzonden. Een klik verstuurt niets.'),
 dict(title='4 · Fictieve registratie',text='Alleen scenario: 1,5 uur × € 60,00 = € 90,00; 1 cilinder × € 150,00 = € 150,00. Totaal € 240,00 excl. btw. W105 blijft open; er zijn geen uren of materialen werkelijk geboekt.'),
 dict(title='5 · Conceptfactuur CF105',text='Concept € 240,00 excl. btw + 21% btw € 50,40 = € 290,40 incl. btw. Niet definitief, niet verzonden, niet in omzet/open facturen opgenomen.'),
 dict(title='6 · Boekhoudinformatie',text='Voorstel na uitvoering: debiteuren € 290,40; omzet arbeid € 90,00; omzet materiaal € 150,00; btw € 50,40. Bij latere betaling: bank aan debiteuren. Geen boeking/export uitgevoerd; geen voorraadkostprijs beschikbaar. Bekijk de interactieve workflow voor getelde demo-acties en expliciete illustratieve aannames.')]
def money(c):return ('€ '+f'{c/100:.2f}').replace('.',',')
def dashboard():
 from workflow import view,dutch_date
 import copy
 w=view();story=copy.deepcopy(STORY);orders=copy.deepcopy(ORDERS);stock=copy.deepcopy(STOCK);followup=copy.deepcopy(FOLLOWUP);actions=copy.deepcopy(ACTIONS)
 for o in orders:
  if o['id'] in {'W104','W106'}:
   j=w.get('jobs',{}).get(o['id'],{})
   o.update(status=j.get('status',o['status']),employee=j.get('responsible',o['employee']))
   if j.get('accepted'):o['job']=j.get('order',{}).get('scope',o['job'])
 for o in orders:
  plan=w.get('jobs',{}).get(o['id'],{}).get('planning')
  if plan:o.update(time=dutch_date(plan['appointment']),employee=plan['employee'])
 for o in w.get('operations',{}).get('orders',{}).values():orders.append(dict(id=o['id'],customer=o['customer'],job=o['scope'],employee=o.get('employee','Niet toegewezen'),time=o.get('appointment','Nog inplannen'),cents=0,status=w.get('jobs',{}).get(o['id'],{}).get('status',o['status'])))
 from business import job_status
 for o in orders:o['status']=job_status(w,o['id'],o['status'])
 orders[4].update(time=dutch_date(w["appointment"]),status=w["status"])
 stock[0].update(available=1 if w["delivery_status"]=="ontvangen" else 0,delivery=dutch_date(w["delivery_at"])+" — "+w["delivery_status"],message=w["message"])
 followup[0]["text"]=w["todo"]["Eigenaar"]+" Contact: "+w["contact"]
 actions[0].update(text="W105: "+w["status"]+". "+w["next_step"]["text"],employee=w["next_step"]["role"])
 inventory=copy.deepcopy(stock)
 stock=[item for item in stock if item['available']<item['required']]
 if w['contact']=='fictief akkoord':followup=[item for item in followup if item['order']!='W105']
 if w['reviewed']:actions=[item for item in actions if item['order']!='W105']
 story[0]['text']='W105 · Atelier Noord (fictief) · Bram · afspraak '+dutch_date(w['appointment'])+' · '+w['status']
 story[1]['text']=inventory[0]['part']+' · '+inventory[0]['delivery']+' · verantwoordelijk: Lina'
 story[2]['text']=w['message']
 story[3]['text']='Gedeelde registratie: '+str(w['hours'])+' uur en '+str(w['materials'])+' cilinder. Nog niet opgeslagen.' if not w['registered'] else 'Opgeslagen door Bram: '+str(w['hours'])+' uur en '+str(w['materials'])+' cilinder. Administratie gebruikt dezelfde velden.'
 story[4]['text']=w['invoice']['id']+' · '+money(w['invoice']['net_cents'])+' excl. btw + '+money(w['invoice']['vat_cents'])+' btw = '+money(w['invoice']['total_cents'])+' incl. btw. '+w['invoice']['status']
 story[5]['text']=w['metrics']['assumption']+' Geen boeking of export.'
 ledger=copy.deepcopy(INVOICES)
 for job_id,job in w.get('jobs',{}).items():
  inv=job.get('sales_invoice')
  if inv and inv['status']!='concept':
   ledger=[i for i in ledger if i['id']!=inv['id']]
   ledger.append(dict(id=inv['id'],order=job_id,net_cents=inv['net_cents'],vat_cents=inv['vat_cents'],due=inv['due'],paid_cents=inv['paid_cents'],status=inv['status'],issued_date=inv.get('issued_date'),credits_cents=sum(c['total_cents'] for c in inv.get('credits',[])),credit_net_cents=sum(c['net_cents'] for c in inv.get('credits',[])),refunded_cents=sum(p['cents'] for p in inv.get('refunds',[]))))
 followup=[item for item in followup if not w.get('jobs',{}).get(item['order'],{}).get('accepted')]
 for item in followup:
  if item['order']=='W106':item['text']='Offerte opvolgen op '+w.get('jobs',{}).get('W106',{}).get('followup_date','2026-10-28')
 for o in orders:
  if o['id']=='W106' and not w.get('jobs',{}).get('W106',{}).get('accepted'):o['status']+=' · opvolgen '+dutch_date(w.get('jobs',{}).get('W106',{}).get('followup_date','2026-10-28'))
 for sale in w.get('operations',{}).get('sales',{}).values():ledger.append(dict(id=sale['id'],order='winkelbalie',net_cents=sale['net_cents'],vat_cents=sale['vat_cents'],due=DAY,paid_cents=sale['paid_cents']))
 for job_id,job in w.get('jobs',{}).items():
  for inv in job.get('invoice_archive',[]):
   ledger=[i for i in ledger if i['id']!=inv['id']]
   ledger.append(dict(inv,order=job_id,credits_cents=sum(c['total_cents'] for c in inv.get('credits',[])),credit_net_cents=sum(c['net_cents'] for c in inv.get('credits',[])),refunded_cents=sum(p['cents'] for p in inv.get('refunds',[]))))
 payments=[dict(p,method='bank',kind='payment',order=next(i['order'] for i in INVOICES if i['id']==p['invoice'])) for p in copy.deepcopy(PAYMENTS) if not any(inv.get('legacy') and inv['id']==p['invoice'] for j in w.get('jobs',{}).values() for inv in [j.get('sales_invoice',{})]+j.get('invoice_archive',[]))]
 for sale in w.get('operations',{}).get('sales',{}).values():payments.append(dict(id='P'+sale['id'],invoice=sale['id'],cents=sale['paid_cents'],date=sale.get('date'),method='cash',kind='sale_payment',order='winkelbalie'))
 for job_id,job in w.get('jobs',{}).items():
  for inv in [job.get('sales_invoice',{})]+job.get('invoice_archive',[]):
   for k,pay in enumerate(inv.get('payments',[])):
    payments.append(dict(pay,id=__import__('improvements').payment_id(inv,k),invoice=inv['id'],order=job_id,kind='payment'))
    if pay.get('reversal'):payments.append(dict(id=__import__('improvements').payment_id(inv,k)+'-REV',invoice=inv['id'],cents=-pay['cents'],date=pay['reversal']['date'],method=pay.get('method','unspecified'),order=job_id,kind='payment_reversal',parent_payment=__import__('improvements').payment_id(inv,k),reason=pay['reversal'].get('reason')))
   for pay in inv.get('refunds',[]):payments.append(dict(pay,invoice=inv['id'],cents=-pay['cents'],order=job_id,kind='refund'))
 for sale in w.get('operations',{}).get('sales',{}).values():
  for ret in sale.get('returns',[]):
   payments.append(dict(id=ret['id'],invoice=sale['id'],cents=-ret['total_cents'],date=ret['date'],method='cash',kind='sale_refund',order='winkelbalie'))
   row=next(i for i in ledger if i['id']==sale['id']);row['credits_cents']=row.get('credits_cents',0)+ret['total_cents'];row['credit_net_cents']=row.get('credit_net_cents',0)+ret['net_cents'];row['refunded_cents']=row.get('refunded_cents',0)+ret['total_cents']
 invoices=[dict(i,total_cents=i['net_cents']+i['vat_cents'],open_cents=i['net_cents']+i['vat_cents']-i.get('credits_cents',0)-i['paid_cents']+i.get('refunded_cents',0),overdue=i['due']<DAY and i['net_cents']+i['vat_cents']-i.get('credits_cents',0)-i['paid_cents']+i.get('refunded_cents',0)>0) for i in ledger]
 result = dict(business='Sleutelhuis Demo',day=DAY,timezone='Europe/Amsterdam',currency='EUR',staff=STAFF,orders=orders,invoices=invoices,payments=payments,stock=stock,inventory=inventory,next_step=w['next_step'],followup=followup,actions=actions,story=story,revenue_cents=sum(i['net_cents']-i.get('credit_net_cents',0) for i in invoices),payments_cents=sum(p['cents'] for p in payments),open_cents=sum(i['open_cents'] for i in invoices),overdue_cents=sum(i['open_cents'] for i in invoices if i['overdue']),planned_count=sum(o['status']!='afgerond' for o in ORDERS),problems=stock,done_actions=0)
 owner_overview(result,w)
 for inv in result['invoices']:
  inv['accounting']=w.get('jobs',{}).get(inv['order'],{}).get('accounting',{'state':'pending'})
  inv['dossier_state']=w.get('jobs',{}).get(inv['order'],{}).get('state')
 for payment in payments:
  payment['customer']=next((i['customer'] for i in result['invoices'] if i['id']==payment['invoice']),'Klant onbekend')
  payment['channel']=payment.get('method') if payment.get('method') in {'bank','cash','card'} else 'unspecified'
 receipts=[pay for pay in payments if pay['kind'] not in {'refund','sale_refund'}]
 channels={k:sum(pay['cents'] for pay in receipts if pay['channel']==k) for k in ['bank','cash','card','unspecified']}
 refunds=-sum(pay['cents'] for pay in payments if pay['kind'] in {'refund','sale_refund'})
 reversals=-sum(pay['cents'] for pay in receipts if pay['kind']=='payment_reversal')
 result['owner']['payment_channels']=channels
 result['receipts']=dict(definition='Netto ontvangen geld na terugboekingen en terugbetalingen, inclusief btw',channels=channels,gross_cents=sum(channels.values()),refund_cents=refunds,reversal_cents=reversals,net_cents=sum(channels.values())-refunds)
 assert result['receipts']['net_cents']==result['payments_cents']
 result['insight']=dict(margin_cents=None,reason='Inkoopkostprijzen, loonkosten en overhead ontbreken; marge niet berekend',net_revenue_cents=result['revenue_cents'],concept_net_cents=sum(j.get('sales_invoice',{}).get('net_cents',0) for j in w.get('jobs',{}).values() if j.get('sales_invoice',{}).get('status')=='concept'))
 from improvements import payment_attention
 projected=__import__('copy').deepcopy(w)
 from improvements import invoice
 for old in INVOICES:invoice(projected,old['order'])
 result['payment_attention']=payment_attention(projected)
 return result

def accounting_csv():
 """Canonical auditable records; no package-specific import or external posting."""
 import csv,io,json,hashlib,copy
 from workflow import load
 from improvements import balance,invoice,payment_id
 s=copy.deepcopy(load());out=io.StringIO();writer=csv.writer(out,delimiter=';')
 header=['record_type','id','original_invoice','parent_payment','order','date','due','net_cents','vat_cents','total_cents','received_cents','credit_cents','refund_cents','open_cents','currency','customer','method','reference_or_reason','accounting_state','source_sha256','metadata_status','missing_fields','required_mappings','net_received_cents','cashflow_effect_cents']
 writer.writerow(header)
 customers={o['id']:o['customer'] for o in ORDERS};customers.update({k:o['customer'] for k,o in s.get('operations',{}).get('orders',{}).items()})
 for old in INVOICES:invoice(s,old['order'])
 for job,j in s.get('jobs',{}).items():
  for inv in j.get('invoice_archive',[])+[j.get('sales_invoice',{})]:
   if not inv or inv['status']=='concept':continue
   b=balance(inv);digest=hashlib.sha256(json.dumps(inv,sort_keys=True).encode()).hexdigest();account=j.get('accounting',{});state=account.get('state','pending') if account.get('invoice',inv['id'])==inv['id'] else 'pending'
   def row(kind,ident,day,net='',vat='',total='',method='',ref='',parent='',source_status='',missing=''):
    writer.writerow([kind,ident,inv['id'],parent,job,day or 'UNKNOWN',inv.get('due','UNKNOWN'),net,vat,total,b['received_cents'],b['credits_cents'],b['refunded_cents'],b['open_cents'],'EUR',customers.get(job,''),method or 'UNKNOWN',ref or 'UNKNOWN',state,digest,source_status,missing,'debiteur_id|dagboek|grootboek|btw_code; centen naar decimalen; bron controleren',b['received_cents']-b['refunded_cents'],total if kind in {'payment','payment_reversal','refund'} else 0])
   row('invoice',inv['id'],inv.get('issued_date'),inv['net_cents'],inv['vat_cents'],inv['total_cents'],ref=inv.get('replaces'),missing='issued_date' if not inv.get('issued_date') else '')
   for cr in inv.get('credits',[]):row('credit',cr['id'],cr['date'],-cr['net_cents'],-cr['vat_cents'],-cr['total_cents'],ref=cr['reason'])
   for n,pay in enumerate(inv.get('payments',[])):
    pid=payment_id(inv,n);missing='|'.join(k for k in ['date','method','reference'] if not pay.get(k));status=pay.get('source_status') or ('unverified' if missing else 'recorded')
    row('payment',pid,pay.get('date'),total=pay['cents'],method=pay.get('method'),ref=pay.get('reference'),source_status=status,missing=missing)
    if pay.get('reversal'):row('payment_reversal',pid+'-REV',pay['reversal']['date'],total=-pay['cents'],parent=pid,ref=pay['reversal']['reason'])
    for index,edit in enumerate(pay.get('metadata_history',[])):row('payment_metadata',pid+'-M'+str(index+1),edit['at'][:10],parent=pid,ref=edit['reason']+' · '+json.dumps(dict(before=edit['before'],after=edit['after']),ensure_ascii=False),source_status=edit['after']['source_status'])
   for pay in inv.get('refunds',[]):row('refund',pay['id'],pay['date'],total=-pay['cents'],method=pay['method'],ref=pay['reference'])
 for sale in s.get('operations',{}).get('sales',{}).values():
  digest=hashlib.sha256(json.dumps(sale,sort_keys=True).encode()).hexdigest()
  def sale_row(kind,ident,net='',vat='',total='',ref='',day=None):
   writer.writerow([kind,ident,sale['id'],'','winkelbalie',day or 'UNKNOWN','',net,vat,total,sale['paid_cents'],sum(r['total_cents'] for r in sale.get('returns',[])),sum(r['total_cents'] for r in sale.get('returns',[])),0,'EUR','Winkelbalie','cash',ref,'pending',digest,'recorded' if day else 'unverified','date' if not day else '','kasdagboek|grootboek|btw_code',sale['paid_cents']-sum(r['total_cents'] for r in sale.get('returns',[])),total if kind in {'sale_payment','sale_refund'} else 0])
  sale_row('sale',sale['id'],sale['net_cents'],sale['vat_cents'],sale['total_cents'],ref=sale['source'],day=sale.get('date'))
  sale_row('sale_payment','P'+sale['id'],total=sale['paid_cents'],ref='Fictieve contante verkoop '+sale['id'],day=sale.get('date'))
  for r in sale.get('returns',[]):
   sale_row('sale_return',r['id'],-r['net_cents'],-r['vat_cents'],-r['total_cents'],r['reason'],r['date'])
   sale_row('sale_refund',r['id']+'-T',total=-r['total_cents'],ref=r['reason'],day=r['date'])
 return ('\ufeff'+out.getvalue()).encode('utf-8')


def owner_overview(d,w):
 """Read model only: preserve stored facts and distinguish unknown values."""
 jobs=w.get('jobs',{});ops=w.get('operations',{});records=[]
 for o in d['orders']:
  ident=o['id'];j=jobs.get(ident,{});op=ops.get('orders',{}).get(ident,{})
  inv=next((i for i in d['invoices'] if i['order']==ident),None)
  quote=(ident=='W106' or op.get('kind')=='offerte') and not j.get('accepted')
  completed=j.get('completed',False) or o['status']=='afgerond' or (ident=='W105' and w['registered'])
  at=(j.get('followup_planning') or j.get('planning') or {}).get('appointment') or op.get('appointment')
  if ident=='W105':at=w['appointment']
  if not at and ident not in {'W104','W106'} and ident not in ops.get('orders',{}):at=DAY+'T'+o['time']
  # No remaining appointment inferred from historical W104 time or W106 follow-up.
  budget=j.get('quote',{}).get('net_cents') if ident=='W106' or op.get('kind')=='offerte' else (o.get('cents') if o.get('cents') else None)
  records.append(dict(state=j.get('state'),id=ident,customer=o['customer'],address=op.get('address') or j.get('address'),phone=op.get('phone'),access=op.get('access'),duration_minutes=((j.get('followup_planning') or j.get('planning') or {}).get('duration_minutes') or op.get('duration_minutes')),job=o['job'],
   employee=(j.get('followup_planning') or j.get('planning') or {}).get('employee') or op.get('employee') or o['employee'],
   priority=op.get('priority'),appointment=at,status=w['status'] if ident=='W105' else o['status'],category='cancelled' if j.get('cancelled') else 'quote' if quote else 'invoiced' if inv else 'to_invoice' if completed else 'open',
   budget_cents=budget,invoiced_cents=inv['net_cents'] if inv else None,invoice=inv['id'] if inv else None,
   due=j.get('followup_date') if quote else None))
 customers={r['id']:r['customer'] for r in records}
 for inv in d['invoices']:inv['customer']=customers.get(inv['order'],'Winkelbalie')
 attention=[]
 for r in records:
  if r['category']=='to_invoice':attention.append(dict(order=r['id'],text=w['status'] if r['id']=='W105' else 'Maak facturatie gereed',responsible='Administratie',deadline=None))
  elif r['category']=='quote':attention.append(dict(order=r['id'],text='Offerte opvolgen'+(' · prijsbron ontbreekt' if not r['budget_cents'] else ''),responsible=r['employee'],deadline=r['due']))
  elif r['category']=='open' and not r['appointment']:attention.append(dict(order=r['id'],text='Plan deze opdracht',responsible='Eigenaar',deadline=None,action='plan'))
 if w['next_step']['action'] and not w['registered']:attention.append(dict(order='W105',text=w['next_step']['text'],responsible=w['next_step']['role'],deadline=w['appointment']))
 for inv in d['invoices']:
  inv['followup']=ops.get('invoice_followups',{}).get(inv['id'])
  if inv['overdue']:attention.append(dict(order=inv['order'],invoice=inv['id'],text='Controleer vervallen saldo '+money(inv['open_cents']),responsible=(inv['followup'] or {}).get('responsible','Administratie'),deadline=(inv['followup'] or {}).get('next_date',inv['due']),action='invoice_followup'))
 for r in records:
  if r.get('priority')=='spoed' and r['category']=='open':attention.append(dict(order=r['id'],text=r['job'],responsible=r['employee'],deadline=r['appointment'],urgent=True))
 for ident,j in w.get('jobs',{}).items():
  part=j.get('waiting_part')
  if not part or part.get('status')=='geannuleerd':continue
  if j.get('completed'):continue
  attention=[a for a in attention if a['order']!=ident or a.get('invoice')]
  state=part.get('status','behoefte geregistreerd');contact=j.get('customer_followup')
  text=('Onderdeel binnen — vervolgafspraak maken: ' if state=='ontvangen' and not j.get('followup_planning') else 'Vervolgafspraak gepland: ' if state=='ontvangen' else 'Blokkade: ')+part['part']+' · '+state+' · levering '+(part.get('expected_delivery') or 'onbekend')+' · '+part['supplier']+' · vervolgafspraak '+('gepland; controleer klantakkoord' if j.get('followup_planning') else 'nog plannen; diagnosebezoek behouden')+' · klantbericht: '+(contact.get('status','concept nog vastleggen')+' · '+contact.get('message','nog geen klantconcept') if contact else 'concept nog vastleggen; niets verzonden')
  if j.get('completed'):continue
  if ident=='W107':
   if contact and not contact.get('review_required') and contact.get('status')!='concept':continue
   text='Lina: bevestig vervolgafspraak'
  attention.append(dict(order=ident,text=text,responsible='Lina' if ident=='W107' else part['responsible'],deadline=part['followup_date'],action='customer_followup' if ident=='W107' else 'part_workflow',urgent=any(r['id']==ident and r.get('priority')=='spoed' for r in records)))
 # Enrich priorities with evidence, without inventing missing dates or deadlines.
 from datetime import date,timedelta,datetime
 from zoneinfo import ZoneInfo
 rule=ops.get('invoice_rule')
 for a in attention:
  record=next((r for r in records if r['id']==a['order']),{})
  a['customer']=record.get('customer','Klant onbekend')
  inv=next((i for i in d['invoices'] if i['id']==a.get('invoice')),None)
  a['amount_cents']=inv['open_cents'] if inv else None;a['amount_label']='Open incl. btw'
  if record.get('category')=='to_invoice' and not inv:
   job=jobs.get(a['order'],{});completed=job.get('completed_date');source=job.get('completion_source','Vastgelegde gereeddatum')
   if not completed:
    history=next((h for h in reversed(w.get('history',[])) if h.get('job')==a['order'] and h.get('action') in {'finish','handoff','register'} and h.get('at')),None)
    if history:
     candidate=datetime.fromisoformat(history['at']).astimezone(ZoneInfo('Europe/Amsterdam')).date().isoformat()
     if candidate<=DAY:completed=candidate;source='Datum historische gereedmelding; uitvoeringsdatum niet afzonderlijk vastgelegd'
   a.update(completed_date=completed,completion_source=source if completed else None,waiting_days=(date.fromisoformat(DAY)-date.fromisoformat(completed)).days if completed else None,action='invoice_ready')
   concept=job.get('sales_invoice',{})
   a['amount_cents']=concept.get('net_cents') if concept.get('status')=='concept' else None;a['amount_label']='Concept excl. btw'
   a['deadline']=(date.fromisoformat(completed)+timedelta(days=rule['days'])).isoformat() if completed and rule else None
  due=(a.get('deadline') or '')[:10]
  blocked=a.get('action')=='part_workflow' and ('Blokkade:' in a['text'] or 'vervolgafspraak maken' in a['text'])
  group='spoed' if a.get('urgent') else 'vervallen' if a.get('invoice') or due and due<DAY else 'geblokkeerd' if blocked else 'administratie'
  a['priority_group']=group;a['priority_reason']={'spoed':'Expliciet als spoed geregistreerd','vervallen':'Factuur vervallen' if a.get('invoice') else 'Vastgelegde actiedatum verstreken','geblokkeerd':'Onderdeel of vervolgplanning houdt uitvoering tegen','administratie':'Volgende administratieve handeling'}[group]
  if a.get('action')=='invoice_ready':a['priority_reason']+=' · factureren binnen '+str(rule['days'])+' dagen na gereedmelding' if rule else ' · facturatieregel nog instellen'
 priority=lambda a:({'spoed':0,'vervallen':1,'geblokkeerd':2,'administratie':3,'inrichting':4}[a['priority_group']],a.get('deadline') or '9999',a.get('completed_date') or '9999',a['order'])
 unique={}
 for a in sorted(attention,key=priority):unique.setdefault(('invoice',a['invoice']) if a.get('invoice') else ('work',a['order']),a)
 attention=list(unique.values())
 if any(r['category']=='to_invoice' for r in records) and not rule:
  attention.append(dict(order='setup-invoice-rule',customer='Facturatie-inrichting',text='Bepaal wanneer gereed werk moet worden gefactureerd',responsible='Eigenaar',deadline=None,action='invoice_rule',priority_group='inrichting',priority_reason='Geen facturatieregel vastgelegd',amount_cents=None))
 channels={'bank':sum(p['cents'] for p in PAYMENTS),'cash':sum(s['paid_cents'] for s in ops.get('sales',{}).values()),'unspecified':sum(p['cents'] for j in jobs.values() for p in j.get('sales_invoice',{}).get('payments',[]))}
 d['owner']=dict(receipts_period=dict(start=min([p['date'] for p in d['payments'] if p.get('date')]+[DAY]),end=max([p['date'] for p in d['payments'] if p.get('date')]+[DAY])),records=records,attention=attention,payment_channels=channels,
  today=[r for r in records if r['category']=='open' and (r['appointment'] or '').startswith(DAY)],
  stock=[dict(key=k,quantity=q,free=q-sum(r['quantity'] for r in ops.get('reservations',{}).values() if r['key']==k and r['status']=='gereserveerd')) for k,q in ops.get('stock',{}).items()])
 from business import availability
 d['owner']['availability']=availability(w,DAY)
 for available in d['owner']['availability']:
  if not available['shift']:
   attention.append(dict(order='setup-roster-'+available['employee'],employee=available['employee'],customer=available['employee'],text='Rooster ontbreekt · capaciteit onbekend',responsible='Eigenaar',deadline=None,action='work_pattern',priority_group='inrichting',priority_reason='Werktijden nodig voor capaciteitsberekening',amount_cents=None))
 d['owner']['invoice_rule']=rule

 d['owner']['availability_by_day']={day:availability(w,day) for day in set([(__import__('datetime').date.fromisoformat(DAY)+__import__('datetime').timedelta(days=n)).isoformat() for n in range(15)]+list(ops.get('worktimes',{}))+[b['day'] for b in ops.get('timeblocks',{}).values()]+[plan['appointment'][:10] for j in jobs.values() for plan in [j.get('planning',{}),j.get('followup_planning',{})] if plan.get('appointment')])}
 d['planned_count']=len(d['owner']['today'])

