"""Local demo corrections. Append-only financial events; no external transport."""
from datetime import date,datetime,timezone
from decimal import Decimal,ROUND_HALF_UP
import copy,hashlib,json
ACTIONS={'payment_metadata', 'payment','payment_reverse','credit','refund','invoice_replace','admin_reopen','accounting_mark','reservation_release','material_return','sale_return','purchase_partial','part_receive','purchase_receive','order_cancel','direct_agreement'}
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
   inv=copy.deepcopy(old);inv.update(total_cents=old['net_cents']+old['vat_cents'],status='verstuurd (gesimuleerd)',legacy=True,lines=[dict(description='Historisch totaal (specificatie ontbreekt)',quantity=1,unit_cents=old['net_cents'],net_cents=old['net_cents'],source='Bestaande demofactuur',vat_percent=21)],payments=[dict(p,method='bank',reference=None,source_status='unverified',simulated=True) for p in PAYMENTS if p['invoice']==old['id']]);j['sales_invoice']=inv
 return j,j.get('sales_invoice')

def change(s,v):
 a=v['action'];job=v.get('job');ops=s.setdefault('operations',{})
 for key in ['orders','stock','purchases','reservations','sales']:ops.setdefault(key,{})
 events=ops.setdefault('events',[])
 def event(**kw):events.append(dict(id='E'+str(len(events)+1),kind=a,date=date.today().isoformat(),**stamp(v),**kw))
 if a in {'reservation_release','material_return'}:
  if v['role'] not in {'Eigenaar','Bram','Lina'}:raise ValueError('Materiaal hoort bij eigenaar / monteur / winkel')
  r=ops['reservations'].get(v.get('reservation'))
  if not r or r['order']!=job:raise ValueError('Kies reservering uit dit dossier')
  reason=required(v,'reason');j=s.get('jobs',{}).get(job,{})
  if a=='reservation_release':
   if r['status']!='gereserveerd':raise ValueError('Reservering al afgehandeld')
   r.update(status='vrijgegeven',reason=reason)
  else:
   if r['status']!='verbruikt':raise ValueError('Verbruik al geretourneerd of niet gevonden')
   if j.get('sales_invoice'):
    inv=j['sales_invoice'];cr=next((c for c in inv.get('credits',[]) if c['id']==v.get('credit_id')),None)
    cost=r['quantity']*r.get('unit_cents',0)
    if inv['status']=='concept' or not cr or not cost or cr['net_cents']-cr.get('material_allocated_cents',0)<cost:raise ValueError('Materiaalretour na facturatie vereist een toereikende creditreferentie; concept eerst corrigeren')
    cr['material_allocated_cents']=cr.get('material_allocated_cents',0)+cost;r['return_credit_id']=cr['id']
   ops['stock'][r['key']]=ops['stock'].get(r['key'],0)+r['quantity'];r.update(status='geretourneerd',reason=reason)
  event(order=job,reservation=r['id'],reason=reason);return
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
   w.update(status=p['status'],received_date=date.today().isoformat());j['followup_required']=True
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
 j,inv=invoice(s,job)
 if not inv or inv['status']=='concept':raise ValueError('Kies een definitieve factuur')
 if a=='admin_reopen':
  if not j.get('administrative_closed'):raise ValueError('Dossier is niet afgesloten')
  reason=required(v,'reason');j.setdefault('closure_history',[]).append(dict(closed=j.pop('administrative_closed'),reason=reason,**stamp(v)));j['status']=dossier_state(s,job)['label'];event(order=job,reason=reason);return
 if j.get('administrative_closed'):raise ValueError('Heropen afgesloten dossier eerst met reden')
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
 accounting=j.get('accounting') or {};book={'pending':'Nog te verwerken','exported':'Geëxporteerd; verwerking onbevestigd','confirmed':'Verwerking handmatig bevestigd','error':'Afstemming nodig'}.get(accounting.get('state','pending'),'Nog te verwerken')
 work='Geannuleerd' if j.get('cancelled') else 'Administratief afgerond' if closed else 'Opnieuw in behandeling' if j.get('closure_history') else 'Uitvoering gereed' if j.get('completed') else 'In behandeling'
 result=dict(work=work,invoice='Nog geen factuur',payment='Nog niet van toepassing',accounting=book,accounting_reference=accounting.get('reference'),accounting_error=accounting.get('reason'),balance=None,financial_difference_cents=0,metadata_unknown=0,responsible='Administratie' if inv or j.get('completed') else j.get('responsible','Eigenaar'),closed=closed)
 if not inv:
  result['label']=work;return result
 b=balance(inv);result['balance']=b
 result['invoice']='Conceptfactuur' if inv['status']=='concept' else 'Definitieve factuur; nog niet verzonden' if inv['status']=='definitief' else 'Factuur verzonden (gesimuleerd)'
 payments=inv.get('payments',[]);active=sum(p['cents'] for p in payments if not p.get('reversal'))
 difference=inv.get('paid_cents',0)-active
 result['financial_difference_cents']=difference
 result['metadata_unknown']=sum(not p.get('date') or not p.get('method') or not p.get('reference') or p.get('source_status')=='unverified' for p in payments)
 result['payment']='Financieel verschil: afstemmen' if difference else 'Klanttegoed: terugbetalen' if b['open_cents']<0 else 'Open saldo' if b['open_cents']>0 else 'Financieel afgehandeld'
 result['label']=work+' · '+(result['invoice'] if inv['status']=='concept' else result['payment'])
 return result
