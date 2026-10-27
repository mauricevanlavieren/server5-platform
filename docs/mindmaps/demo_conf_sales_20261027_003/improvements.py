"""Local demo corrections. Append-only financial events; no external transport."""
from data import DAY
from datetime import date,datetime,timezone
from decimal import Decimal,ROUND_HALF_UP
import copy,hashlib,json
ACTIONS={'tour_prepare','invoice_date','invoice_rule','completion_date','work_pattern','payment_metadata', 'payment','payment_reverse','credit','refund','invoice_replace','admin_reopen','accounting_mark','reservation_release','material_return','sale_return','purchase_partial','part_receive','purchase_receive','order_cancel','direct_agreement'}
def stamp(v):return dict(role=v['role'],at=datetime.now(timezone.utc).isoformat())
def required(v,key):
 x=v.get(key)
 if not isinstance(x,str) or not x.strip() or len(x)>1000:raise ValueError('Vul '+key+' in')
 return x.strip()
def amount(v,key='cents'):
 x=v.get(key)
 if type(x) is not int or not 0<x<=100000000:raise ValueError('Vul een positief bedrag / aantal in')
 return x

def day(v,key='date'):
 x=required(v,key)
 try:date.fromisoformat(x)
 except ValueError:raise ValueError('Kies een geldige datum')
 return x

def balance(inv):
 credits=sum(c['total_cents'] for c in inv.get('credits',[]))
 received=inv.get('paid_cents',0)
 refunded=sum(p['cents'] for p in inv.get('refunds',[]))
 return dict(credits_cents=credits,received_cents=received,refunded_cents=refunded,open_cents=inv['total_cents']-credits-received+refunded)

def invoice(s,job):
 j=s.setdefault('jobs',{}).setdefault(job,{})
 if not j.get('sales_invoice'):
  from data import INVOICES,PAYMENTS
  old=next((i for i in INVOICES if i['order']==job),None)
  if old:
   inv=copy.deepcopy(old);inv.update(total_cents=old['net_cents']+old['vat_cents'],status='verstuurd (gesimuleerd)',legacy=True,lines=[dict(description='Historisch totaal (specificatie ontbreekt)',quantity=1,unit_cents=old['net_cents'],net_cents=old['net_cents'],source='Bestaande demofactuur',vat_percent=21)],payments=[dict(p,method='bank',reference=None,source_status='unverified',simulated=True) for p in PAYMENTS if p['invoice']==old['id']]);j['sales_invoice']=inv;j.setdefault('completed',True);j['legacy']=True
 return j,j.get('sales_invoice')

def change(s,v):
 a=v['action'];job=v.get('job');ops=s.setdefault('operations',{})
 for key in ['orders','stock','purchases','reservations','sales']:ops.setdefault(key,{})
 events=ops.setdefault('events',[])
 def event(**kw):events.append(dict(id='E'+str(len(events)+1),kind=a,date=date.fromisoformat(DAY).isoformat(),**stamp(v),**kw))
 if a=='tour_prepare':
  if v['role']!='Eigenaar':raise ValueError('Een oefenronde wordt door de eigenaar klaargezet')
  from sales import prepare
  prepare(s,v);return
 if a=='work_pattern':
  if v['role'] not in {'Eigenaar','Lina'}:raise ValueError('Werkrooster hoort bij eigenaar / planning')
  from datetime import time
  employee=v.get('employee');days=v.get('days');start=required(v,'start');end=required(v,'end')
  if employee not in {'Noor','Lina','Bram'} or not isinstance(days,list) or not days or any(type(d) is not int or not 0<=d<=6 for d in days) or len(set(days))!=len(days):raise ValueError('Kies medewerker en unieke weekdagen')
  time.fromisoformat(start);time.fromisoformat(end)
  if len(start)!=5 or len(end)!=5 or start>=end:raise ValueError('Kies geldige begin- en eindtijd')
  source=required(v,'source')
  from business import occupied
  from data import ORDERS
  candidates=ORDERS+list(ops.get('orders',{}).values())
  dates={o['appointment'][:10] for o in candidates if o.get('appointment')}
  for j in s.get('jobs',{}).values():
   for key in ['planning','diagnosis_visit','followup_planning']:
    if j.get(key,{}).get('appointment'):dates.add(j[key]['appointment'][:10])
  for candidate in dates:
   if ops.get('worktimes',{}).get(candidate,{}).get(employee):continue
   for b in occupied(s,candidate):
    if b['employee']==employee and not b.get('kind') and (date.fromisoformat(candidate).weekday() not in days or not b.get('end') or b['appointment'][11:]<start or b['end'][11:]>end):raise ValueError('Rooster sluit een bestaande afspraak uit; controleer dagafwijking eerst')
  old=copy.deepcopy(ops.setdefault('work_patterns',{}).get(employee));ops['work_patterns'][employee]=dict(days=days,start=start,end=end,source=source,**stamp(v));event(employee=employee,before=old,after=ops['work_patterns'][employee]);return
 if a in {'reservation_release','material_return'}:

  if v['role'] not in {'Eigenaar','Bram','Lina'}:raise ValueError('Materiaal hoort bij eigenaar / monteur / winkel')
  r=ops['reservations'].get(v.get('reservation'))
  if not r or r['order']!=job:raise ValueError('Kies reservering uit dit dossier')
  reason=required(v,'reason');j=s.get('jobs',{}).get(job,{})
  expected='gereserveerd' if a=='reservation_release' else 'verbruikt'
  if r['status']!=expected:raise ValueError('Materiaal is al afgehandeld of heeft niet de juiste status')
  qty=v.get('quantity',r['quantity'])
  if type(qty) is not int or not 0<qty<=r['quantity']:raise ValueError('Aantal overschrijdt het nog beschikbare materiaal')
  before=copy.deepcopy(r);inv=j.get('sales_invoice')
  if a=='material_return':
   if inv and inv['status']=='concept':
    original=copy.deepcopy(inv)
    if j.get('billing',{}).get('mode') not in {'fixed','extra'}:
     line=next((line for line in inv['lines'] if line.get('reservation')==r['id']),None)
     if not line or line['quantity']<qty:raise ValueError('Conceptregel niet herleidbaar: corrigeer eerst het concept met bron')
     line['quantity']-=qty;line['net_cents']=line['quantity']*line['unit_cents']
     inv['lines']=[line for line in inv['lines'] if line['quantity']>0]
     inv['net_cents']=sum(line['net_cents'] for line in inv['lines']);inv['vat_cents']=int((Decimal(inv['net_cents'])*Decimal('.21')).quantize(Decimal('1'),rounding=ROUND_HALF_UP));inv['total_cents']=inv['net_cents']+inv['vat_cents']
    j.setdefault('invoice_adjustments',[]).append(dict(before=original,after=copy.deepcopy(inv),reason=reason,quantity=qty,reservation=r['id'],**stamp(v)))
   elif inv:
    cr=next((c for c in inv.get('credits',[]) if c['id']==v.get('credit_id')),None);cost=qty*(r.get('unit_cents') or 0)
    if not cr or not cost or cr['net_cents']-cr.get('material_allocated_cents',0)<cost:raise ValueError('Materiaalretour na facturatie vereist een toereikende creditreferentie')
    cr['material_allocated_cents']=cr.get('material_allocated_cents',0)+cost;r['return_credit_id']=cr['id']
   ops['stock'][r['key']]=ops['stock'].get(r['key'],0)+qty
  r.setdefault('original_quantity',r['quantity']);r['quantity']-=qty
  if not r['quantity']:r['status']='vrijgegeven' if a=='reservation_release' else 'geretourneerd'
  key='released_quantity' if a=='reservation_release' else 'returned_quantity';r[key]=r.get(key,0)+qty;r['reason']=reason
  r.setdefault('transitions',[]).append(dict(action=a,quantity=qty,before_quantity=before['quantity'],remaining_quantity=r['quantity'],reason=reason,credit_id=v.get('credit_id') or None,**stamp(v)))
  event(order=job,reservation=r['id'],quantity=qty,remaining_quantity=r['quantity'],reason=reason);return
 if a=='sale_return':
  if v['role'] not in {'Eigenaar','Lina'}:raise ValueError('Winkelretour hoort bij winkel / eigenaar')
  sale=ops['sales'].get(v.get('sale'));qty=amount(v,'quantity');reason=required(v,'reason')
  if not sale or qty>sale['quantity']-sum(r['quantity'] for r in sale.get('returns',[])):raise ValueError('Retour overschrijdt verkocht / nog niet geretourneerd aantal')
  returns=sale.setdefault('returns',[]);count=sum(r['quantity'] for r in returns)+qty
  total_net=count*sale['unit_cents'];total_vat=int((Decimal(total_net)*Decimal('.21')).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
  ret=dict(id=sale['id']+'-R'+str(len(returns)+1),quantity=qty,net_cents=qty*sale['unit_cents'],vat_cents=total_vat-sum(r['vat_cents'] for r in returns),reason=reason,**stamp(v));ret['total_cents']=ret['net_cents']+ret['vat_cents'];ret['refund_method']='cash';ret['date']=day(v)
  returns.append(ret);ops['stock'][sale['key']]+=qty;event(sale=sale['id'],return_id=ret['id'],refund_cents=ret['total_cents']);return
 if a in {'purchase_partial','part_receive','purchase_receive'}:
  if v['role'] not in {'Eigenaar','Lina'}:raise ValueError('Ontvangst hoort bij winkel / eigenaar')
  j=s.get('jobs',{}).get(v.get('order',job),{});w=j.get('waiting_part',{})
  p=ops['purchases'].get(v.get('purchase') or w.get('purchase_id'))
  if not p or p['status'] in {'ontvangen','geannuleerd'}:raise ValueError('Kies een open inkooporder')
  if p.get('order') and p['status'] not in {'besteld','bevestigd','gedeeltelijk ontvangen'}:raise ValueError('Registreer eerst de fictieve bestelling')
  remaining=p['quantity']-p.get('received_quantity',0);qty=v.get('quantity',remaining)
  if type(qty) is not int or not 0<qty<=remaining:raise ValueError('Ontvangst overschrijdt resterende bestelling')
  key=p['part']+' @ '+p['location'];ops['stock'][key]=ops['stock'].get(key,0)+qty;p['received_quantity']=p.get('received_quantity',0)+qty;p['status']='ontvangen' if qty==remaining else 'gedeeltelijk ontvangen'
  if p.get('order'):
   j=s['jobs'][p['order']];w=j['waiting_part']
   w.update(status=p['status'],received_date=date.fromisoformat(DAY).isoformat());j['followup_required']=True
   if j.get('customer_followup'):j['customer_followup']['review_required']=True
  event(order=p.get('order'),purchase=p['id'],quantity=qty);return
 if a=='order_cancel':
  j=s.setdefault('jobs',{}).setdefault(job,{})
  if v['role'] not in {'Eigenaar','Lina'} or j.get('cancelled') or j.get('sales_invoice') or j.get('completed'):raise ValueError('Annuleer alleen open werk; facturatie eerst afzonderlijk afhandelen')
  if any(r['order']==job and r['status'] in {'gereserveerd','verbruikt'} for r in ops['reservations'].values()) or any(p.get('order')==job and p['status'] not in {'ontvangen','geannuleerd'} for p in ops['purchases'].values()):raise ValueError('Handel materiaal en inkoop eerst af')
  j.update(cancelled=dict(reason=required(v,'reason'),**stamp(v)),status='geannuleerd');event(order=job,reason=j['cancelled']['reason']);return
 if a=='direct_agreement':
  j=s.setdefault('jobs',{}).setdefault(job,{})
  if v['role'] not in {'Eigenaar','Lina','Administratie'} or j.get('sales_invoice') or j.get('cancelled'):raise ValueError('Afspraak vóór facturatie vastleggen')
  j['direct_agreement']=dict(who=required(v,'who'),date=day(v),reference=required(v,'reference'),mode='actual',**stamp(v));event(order=job,agreement=j['direct_agreement']);return
 if v['role'] not in {'Eigenaar','Administratie'}:raise ValueError('Financiële correcties horen bij administratie / eigenaar')
 if a=='invoice_rule':
  if v['role']!='Eigenaar':raise ValueError('Facturatieregel instellen hoort bij de eigenaar')
  days=v.get('days')
  if type(days) is not int or not 0<=days<=90:raise ValueError('Kies 0 tot 90 dagen')
  source=required(v,'source');s.setdefault('operations',{})['invoice_rule']=dict(days=days,source=source,**stamp(v));event(rule=s['operations']['invoice_rule']);return
 if a=='completion_date':
  j=s.setdefault('jobs',{}).setdefault(job,{})
  if not j.get('completed') and not (job=='W105' and s.get('registered')):raise ValueError('Alleen gereedgemeld werk heeft een gereeddatum')
  value=day(v);source=required(v,'source')
  if value>DAY:raise ValueError('Gereeddatum mag niet na de demodag liggen')
  j.setdefault('completion_date_history',[]).append(dict(before=j.get('completed_date'),after=value,source=source,**stamp(v)))
  j['completed_date']=value;j['completion_source']=source;event(order=job,date_value=value,source=source);return
 j,inv=invoice(s,job)
 if a=='invoice_date':
  if v.get('invoice'):
   inv=next((candidate for candidate in [inv]+j.get('invoice_archive',[]) if candidate and candidate['id']==v['invoice']),None)
  if not inv or inv['status']=='concept':raise ValueError('Kies een definitieve historische factuur')
  if inv.get('issued_date'):raise ValueError('Een bekende definitieve factuurdatum wordt niet overschreven')
  value=day(v);source=required(v,'source')
  if value>DAY or value>inv['due']:raise ValueError('Factuurdatum mag niet na demodag of vervaldatum liggen')
  inv.setdefault('date_history',[]).append(dict(before=inv.get('issued_date'),after=value,source=source,**stamp(v)));inv['issued_date']=value
  if j.get('accounting'):j['accounting'].update(state='error',reason='Historische factuurdatum aangevuld; opnieuw afstemmen')
  event(order=job,invoice=inv['id'],date_value=value,source=source);return
 if a=='payment_metadata':
  for candidate in [inv]+j.get('invoice_archive',[]):
   if candidate and any(payment_id(candidate,n)==v.get('payment') for n in range(len(candidate.get('payments',[])))):inv=candidate;break
 if not inv or inv['status']=='concept':raise ValueError('Kies een definitieve factuur')
 if a=='admin_reopen':
  if not j.get('administrative_closed'):raise ValueError('Dossier is niet afgesloten')
  reason=required(v,'reason');j.setdefault('closure_history',[]).append(dict(closed=j.pop('administrative_closed'),reason=reason,**stamp(v)));j['status']=dossier_state(s,job)['label'];event(order=job,reason=reason);return
 if j.get('administrative_closed') and a!='payment_metadata':raise ValueError('Heropen afgesloten dossier eerst met reden')
 b=balance(inv)
 if a=='payment_metadata':
  index=next((n for n,p in enumerate(inv.get('payments',[])) if payment_id(inv,n)==v.get('payment')),None)
  if index is None:raise ValueError('Kies een bestaande betaling')
  p=inv['payments'][index];original=copy.deepcopy(p);reason=required(v,'reason');source_status=v.get('source_status')
  if source_status not in {'verified','unverified'}:raise ValueError('Kies aangetoond of brongegevens ontbreken')
  method=v.get('method','');ref=v.get('reference','').strip();payment_date=v.get('payment_date','')
  if method not in {'','bank','cash','card'} or len(ref)>1000:raise ValueError('Kies bank, kas, pin of onbekend')
  if payment_date:date.fromisoformat(payment_date)
  if source_status=='verified' and (not method or not ref or not payment_date):raise ValueError('Bevestigde bron vereist datum, methode en referentie')
  p.setdefault('id',payment_id(inv,index))
  p.setdefault('metadata_history',[]).append(dict(before={k:val for k,val in original.items() if k!='metadata_history'},after=dict(date=payment_date or None,method=method or None,reference=ref or None,source_status=source_status),reason=reason,**stamp(v)))
  p.update(date=payment_date or None,method=method or None,reference=ref or None,source_status=source_status)
  event(order=job,payment=p['id'],reason=reason,correction='Alleen betaalgegevens; bedrag ongewijzigd')
 elif a=='payment':
  if inv['status']!='verstuurd (gesimuleerd)':raise ValueError('Registreer eerst fictieve verzending')
  value=amount(v)
  if value>b['open_cents']:raise ValueError('Overbetaling geblokkeerd: bedrag groter dan open saldo')
  method=required(v,'method')
  if method not in {'bank','cash','card'}:raise ValueError('Kies bank, kas of pin')
  payments=inv.setdefault('payments',[]);p=dict(id=inv['id']+'-P'+str(len(payments)+1),cents=value,date=day(v),method=method,reference=required(v,'reference'),source_status='verified',simulated=True,**stamp(v));payments.append(p);inv['paid_cents']+=value;event(order=job,payment=copy.deepcopy(p))
 elif a=='payment_reverse':
  index=next((n for n,p in enumerate(inv.get('payments',[])) if payment_id(inv,n)==v.get('payment')),None)
  p=inv['payments'][index] if index is not None else None
  if not p or p.get('reversal'):raise ValueError('Kies een niet-teruggeboekte betaling')
  p.setdefault('id',payment_id(inv,index))
  p['reversal']=dict(reason=required(v,'reason'),date=day(v),**stamp(v));inv['paid_cents']-=p['cents'];event(order=job,payment=p['id'],reversal=p['reversal'])
 elif a=='credit':
  net=amount(v,'net_cents');credits=inv.setdefault('credits',[]);credited=sum(c['net_cents'] for c in credits)
  if net>inv['net_cents']-credited:raise ValueError('Credit groter dan resterend factuurbedrag exclusief btw')
  accumulated=credited+net
  vat=inv['vat_cents'] if accumulated==inv['net_cents'] else int((Decimal(accumulated)*Decimal(inv['vat_cents'])/Decimal(inv['net_cents'])).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
  credit=dict(id=inv['id']+'-C'+str(len(credits)+1),original=inv['id'],net_cents=net,vat_cents=vat-sum(c['vat_cents'] for c in credits),reason=required(v,'reason'),date=day(v),status='definitieve credit (demo)',**stamp(v));credit['total_cents']=net+credit['vat_cents'];credits.append(credit);event(order=job,credit=copy.deepcopy(credit))
 elif a=='refund':
  if v.get('method') not in {'bank','cash','card'}:raise ValueError('Kies bank, kas of pin')
  value=amount(v)
  if value>max(0,-b['open_cents']):raise ValueError('Terugbetaling maximaal het tegoed')
  refund=dict(id=inv['id']+'-T'+str(len(inv.get('refunds',[]))+1),cents=value,date=day(v),method=required(v,'method'),reference=required(v,'reference'),reason=required(v,'reason'),simulated=True,**stamp(v));inv.setdefault('refunds',[]).append(refund);event(order=job,refund=refund)
 elif a=='invoice_replace':
  if b['credits_cents']!=inv['total_cents'] or b['open_cents']!=0:raise ValueError('Crediteer origineel volledig en handel ontvangen geld / tegoed eerst af')
  reason=required(v,'reason');net=amount(v,'net_cents');vat=int((Decimal(net)*Decimal('.21')).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
  j.setdefault('invoice_archive',[]).append(copy.deepcopy(inv));seq=len(j['invoice_archive']);new=dict(id=inv['id'].split('-V')[0]+'-V'+str(seq),replaces=inv['id'],replacement_reason=reason,status='concept',lines=[dict(description='Vervanging '+inv['id'],quantity=1,unit_cents=net,net_cents=net,vat_percent=21,source=reason)],net_cents=net,vat_cents=vat,total_cents=net+vat,paid_cents=0,due=day(v,'due'),replacement=True);j['sales_invoice']=new;event(order=job,original=inv['id'],replacement=new['id'],reason=reason)
 elif a=='accounting_mark':
  state=v.get('state');ref=required(v,'reference')
  if state not in {'exported','confirmed','error'}:raise ValueError('Kies export, bevestiging of afstemmingsfout')
  previous=j.get('accounting',{})
  if state=='confirmed' and previous.get('state') not in {'exported','error'}:raise ValueError('Leg eerst de export vast; downloaden is geen verwerking')
  digest=hashlib.sha256(json.dumps(inv,sort_keys=True).encode()).hexdigest()
  record=dict(state=state,reference=ref,invoice=inv['id'],sha256=digest,date=day(v),**stamp(v));j['accounting']=record;j.setdefault('accounting_history',[]).append(copy.deepcopy(record));event(order=job,accounting=record)
 j['status']=dossier_state(s,job)['label']
 # A correction invalidates an earlier accounting confirmation, without deleting evidence.
 if a not in {'accounting_mark','admin_reopen'} and j.get('accounting'):
  j['accounting']['state']='error';j['accounting']['reason']='Financiële gegevens gewijzigd; opnieuw afstemmen'


def payment_id(inv,index):
 return inv.get('payments',[])[index].get('id') or inv['id']+'-legacy-'+str(index+1)

def dossier_state(s,job):
 """Single read model for work, invoice, payments, accounting and next action."""
 j=s.get('jobs',{}).get(job,{});inv=j.get('sales_invoice');closed=bool(j.get('administrative_closed'))
 accounting=j.get('accounting') or {};book={'pending':'Nog te verwerken','exported':'Geëxporteerd; verwerking onbevestigd','confirmed':'Eigen verklaring; extern bewijs niet gevalideerd','error':'Afstemming nodig'}.get(accounting.get('state','pending'),'Nog te verwerken')
 work='Geannuleerd' if j.get('cancelled') else 'Administratief afgerond' if closed else 'Opnieuw in behandeling' if j.get('closure_history') else 'Uitvoering gereed' if j.get('completed') else 'In behandeling'
 result=dict(work=work,invoice='Nog geen factuur',payment='Nog niet van toepassing',accounting=book,accounting_reference=accounting.get('reference'),accounting_error=accounting.get('reason'),balance=None,financial_difference_cents=0,metadata_unknown=0,historical_metadata_unknown=0,responsible='Administratie' if inv or j.get('completed') else j.get('responsible','Eigenaar'),closed=closed)
 if not inv:
  result['label']=work;return result
 b=balance(inv);result['balance']=b
 result['invoice']='Conceptfactuur' if inv['status']=='concept' else 'Definitieve factuur; nog niet verzonden' if inv['status']=='definitief' else 'Factuur verzonden (gesimuleerd)'
 payments=inv.get('payments',[]);active=sum(p['cents'] for p in payments if not p.get('reversal'))
 difference=inv.get('paid_cents',0)-active
 result['financial_difference_cents']=difference
 all_payments=payments+[p for archived in j.get('invoice_archive',[]) for p in archived.get('payments',[])]
 result['metadata_unknown']=sum(not p.get('date') or not p.get('method') or not p.get('reference') or p.get('source_status')!='verified' for p in all_payments if not p.get('reversal'))
 result['historical_metadata_unknown']=sum(not p.get('date') or not p.get('method') or not p.get('reference') or p.get('source_status')!='verified' for p in all_payments if p.get('reversal'))
 result['payment']='Financieel verschil: afstemmen' if difference else 'Klanttegoed: terugbetalen' if b['open_cents']<0 else 'Open saldo' if b['open_cents']>0 else 'Financieel afgehandeld'
 result['label']=work+' · '+(result['invoice'] if inv['status']=='concept' else result['payment'])
 return result


def payment_attention(s):
 """Active issues only. Reversed registrations remain historical evidence."""
 result=[]
 for job,j in s.get('jobs',{}).items():
  for inv in [j.get('sales_invoice',{})]+j.get('invoice_archive',[]):
   if not inv or inv.get('status')=='concept':continue
   for index,p in enumerate(inv.get('payments',[])):
    missing=[key for key in ['date','method','reference'] if not p.get(key)]
    if not p.get('reversal') and (missing or p.get('source_status')!='verified'):
     result.append(dict(job=job,invoice=inv['id'],payment_id=payment_id(inv,index),cents=p['cents'],date=p.get('date'),method=p.get('method'),reference=p.get('reference'),missing=missing,unverified=p.get('source_status')!='verified',closed=bool(j.get('administrative_closed'))))
 return result
