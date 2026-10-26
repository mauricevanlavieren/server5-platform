"""Fictional local sales ledger. All amounts integer cents; no external actions."""
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

def cents(value):
 return int(Decimal(str(value)).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
def existing_w105(s):
 """Project the existing registered CF105 without changing persisted state."""
 if not s.get('registered'):return None
 hours=s['hours'];materials=s['materials']
 lines=[dict(description='Arbeid W105',quantity=hours,unit_cents=6000,source='Bestaand CF105 · demo-uurtarief',net_cents=cents(Decimal(str(hours))*6000),vat_percent=21)]
 if materials:lines.append(dict(description='Cilinders',quantity=materials,unit_cents=15000,source='Bestaand CF105 · demo-materiaalprijs',net_cents=materials*15000,vat_percent=21))
 net=sum(l['net_cents'] for l in lines);vat=cents(Decimal(net)*Decimal('0.21'))
 return dict(id='CF105',status='concept',reviewed=s.get('reviewed',False),lines=lines,net_cents=net,vat_cents=vat,total_cents=net+vat,paid_cents=0,due=None)

def mutate(s,v):
 a=v['action'];role=v['role'];job=v.get('job')
 if a in {'billing_save','billing_apply','tariff_save'}:
  billing_mutate(s,v);return
 if a=='quote_start':
  op=s.get('operations',{}).get('orders',{}).get(job)
  j=s.setdefault('jobs',{}).setdefault(job,{})
  if role not in {'Eigenaar','Lina'} or not op or op.get('appointment') or j.get('planning') or j.get('completed') or j.get('quote') or j.get('findings'):raise ValueError('Offerte alleen vóór planning/uitvoering van een nieuwe opdracht')
  op['kind']='offerte';j.update(quote=dict(id='O'+job[1:],scope=op['scope']),status='offerteconcept — prijs ontbreekt')
  return
 if a=='admin_close':
  from improvements import balance
  j=s.get('jobs',{}).get(job,{});inv=j.get('sales_invoice') or {}
  if role not in {'Eigenaar','Administratie'} or not j.get('completed') or inv.get('status')!='verstuurd (gesimuleerd)' or balance(inv)['open_cents']!=0 or (not inv.get('payments') and not inv.get('credits')) or j.get('administrative_closed'):raise ValueError('Eerst gereedmelden, controleren, definitief maken, fictief verzenden en volledig fictief betalen')
  if __import__('improvements').dossier_state(s,job)['financial_difference_cents']:raise ValueError('Betalingsregistraties wijken af van ontvangen totaal; stem eerst de brongegevens af')
  if j.get('accounting',{}).get('state')=='error':raise ValueError('Boekhoudafstemming nog open; leg controle en bewijsreferentie vast')
  if invoice_control(s,job)['blocked']:raise ValueError('Factuurcontrole nog geblokkeerd')
  if any(r['order']==job and r['status']=='gereserveerd' for r in s.get('operations',{}).get('reservations',{}).values()):raise ValueError('Open materiaalreservering eerst verwerken')
  if j.get('customer_followup',{}).get('review_required'):raise ValueError('Oud klantconcept eerst beoordelen')
  j.update(administrative_closed=dict(date=date.today().isoformat(),role=role,simulated=True),status='administratief afgerond (demo)',accounting_status='niet gekoppeld')
  return
 if a=='visit_hours':
  if role not in {'Bram','Eigenaar','Administratie'}:raise ValueError('Uren horen bij monteur of administratie')
  j=s.get('jobs',{}).get(job,{})
  inv=j.get('sales_invoice')
  if inv and inv['status']!='concept':raise ValueError('Definitieve factuur beschermt bezoekregistratie')
  if not j.get('diagnosis_visit'):raise ValueError('Geen afzonderlijke bezoeken')
  values=v.get('visit_hours',{});keys=['diagnosis']+(['followup'] if j.get('followup_planning') else [])
  import math
  for key in keys:
   h=values.get(key)
   if h is not None and (type(h) not in (int,float) or not math.isfinite(h) or not 0<=h<=24):raise ValueError('Ongeldige bezoekuren')
  j['visit_hours']={key:values.get(key) for key in keys}
  return
 if a=='plan':
  target=v.get('order');op=s.get('operations',{}).get('orders',{}).get(target,{})
  if op.get('agreement_required') and not s.get('jobs',{}).get(target,{}).get('direct_agreement') and not s.get('jobs',{}).get(target,{}).get('accepted'):raise ValueError('Leg eerst het directe klantakkoord vast')
 if a in OPS:
  operate(s,v);return
 j=s.setdefault('jobs',{}).setdefault(job,{})
 if a=='invoice_revise':
  previous=j.get('sales_invoice')
  if not previous or previous['status']!='concept':raise ValueError('Alleen concept kan worden aangepast')
  if v.get('preserve_materials') is True:
   if role not in {'Administratie','Eigenaar'}:raise ValueError('Tariefwijziging hoort bij administratie')
   rate=v.get('rate_cents');source=v.get('source','').strip()
   if type(rate) is not int or not 0<rate<=1000000 or not source or len(source)>300:raise ValueError('Positief tarief en herleidbare bron vereist')
   labor=previous['lines'][0]
   if not labor['description'].lower().startswith('arbeid'):raise ValueError('Arbeidsregel onduidelijk')
   labor.update(unit_cents=rate,source=source,net_cents=cents(Decimal(str(labor['quantity']))*rate))
   previous['net_cents']=sum(line['net_cents'] for line in previous['lines']);previous['vat_cents']=cents(Decimal(previous['net_cents'])*Decimal('0.21'));previous['total_cents']=previous['net_cents']+previous['vat_cents']
   return
  if len(previous.get('lines',[]))>2:raise ValueError('Meerdere bestaande regels: behoud deze en controleer afzonderlijk; automatisch vervangen geblokkeerd')
  del j['sales_invoice'];mutate(s,dict(v,action='invoice_draft',_revising=True));j['sales_invoice']['id']=previous['id'];
  if job=='W105':s['reviewed']=False
  return
 if a.startswith('quote_'):
  if role not in {'Lina','Eigenaar'} or not (job=='W106' or s.get('operations',{}).get('orders',{}).get(job,{}).get('kind')=='offerte'):raise ValueError('Offerte hoort bij Lina/Henk en W106')
  if a=='quote_save':
   text=v.get('scope','').strip();source=v.get('source','').strip();amount=v.get('net_cents');lines=v.get('lines')
   if lines is not None:
    lines=quote_lines(lines);amount=sum(l['net_cents'] for l in lines);source='Prijsbronnen per offerteregel'
   if not text or len(text)>1000 or not source or len(source)>300:raise ValueError('Omschrijving en herleidbare prijsbron vereist')
   if type(amount) is not int or not 0<amount<=100000000:raise ValueError('Vul een positief offertebedrag in')
   if j.get('accepted'):raise ValueError('Offerte reeds opdracht')
   j.update(quote=dict(id='O'+job[1:],scope=text,source=source,net_cents=amount,vat_percent=21,lines=lines or [dict(description=text,quantity=1,unit_cents=amount,net_cents=amount,source=source,vat_percent=21)]),status='offerte ter opvolging')
  else:
   if not j.get('quote',{}).get('net_cents') or not j['quote'].get('source'):raise ValueError('Offertebedrag en herleidbare prijsbron ontbreken nog')
   if j.get('accepted'):raise ValueError('Opdracht bestaat al')
   if v.get('confirmed') is not True:raise ValueError('Bevestig het fictieve klantakkoord')
   agreement=text_value(v,'agreement',300)
   import copy
   j.update(accepted=True,agreement=agreement,order=dict(copy.deepcopy(j['quote']),id=job),status='opdracht — inplannen',responsible='Eigenaar')
   op=s.get('operations',{}).get('orders',{}).get(job)
   if op:op.update(scope=j['quote']['scope'],status='opdracht — inplannen')
  return
 if role not in {'Administratie','Eigenaar'} or (job not in {'W104','W105'} and job not in s.get('operations',{}).get('orders',{}) and not (job=='W106' and j.get('accepted'))):raise ValueError('Facturatie hoort bij Administratie/Henk en W104')
 if job=='W105' and not j.get('sales_invoice') and s.get('registered') and not v.get('_revising'):
  j['sales_invoice']=existing_w105(s)
 inv=j.get('sales_invoice')
 if a=='invoice_draft':
  if j.get('billing',{}).get('mode') in {'fixed','extra'}:
   if inv or not j.get('completed'):raise ValueError('Eerst gereedmelden; bestaand concept behouden')
   lines=billing_lines(j);net=sum(l['net_cents'] for l in lines);vat=cents(Decimal(net)*Decimal('.21'));due=text_value(v,'due',10);date.fromisoformat(due)
   j['sales_invoice']=dict(id='CF'+job[1:],status='concept',lines=lines,net_cents=net,vat_cents=vat,total_cents=net+vat,paid_cents=0,due=due);return
  if job=='W105' and s.get('registered'):
   j.update(completed=True,hours=s['hours'],materials=(str(s['materials'])+' cilinder(s)' if s['materials'] else 'Geen materiaal: '+s.get('material_reason','')),responsible='Administratie')
  if not j.get('completed'):raise ValueError('Eerst gereedmelden')
  if inv:raise ValueError('Concept bestaat al; geen dubbele factuur')
  rate=v.get('rate_cents');source=v.get('source','').strip()
  if type(rate) is not int or not 0<rate<=1000000 or not source or len(source)>300:raise ValueError('Vul een positief uurtarief en een prijsbron in')
  no_material=j.get('materials','').strip().lower().startswith('geen materiaal') or j.get('materials','').strip().lower() in {'geen','0'}
  proposal=invoice_proposal(s,job)
  if proposal['hours_total'] is None:raise ValueError('Registreer eerst uren per bezoek; onbekend is geen nul')
  net=cents(Decimal(str(proposal['hours_total']))*rate)
  lines=[dict(description='Arbeid '+job,quantity=proposal['hours_total'],unit_cents=rate,source=source,net_cents=net,vat_percent=21)]
  consumed=[r for r in s.get('operations',{}).get('reservations',{}).values() if r['order']==job and r['status']=='verbruikt']
  if no_material and consumed:raise ValueError('Er is materiaalverbruik: registreer en prijs dit eerst correct')
  if consumed:
   prices=v.get('material_prices',{})
   for mat in proposal['materials']:
    price=prices.get(mat['reservation'],{})
    unit=price.get('unit_cents',mat['unit_cents']);price_source=price.get('source',mat['price_source'])
    if type(unit) is not int or not 0<unit<=100000000 or not isinstance(price_source,str) or not price_source.strip():raise ValueError('Materiaalprijs onbekend: leg een positieve verkoopprijs en prijsbron vast voor '+mat['reservation'])
    lines.append(dict(description=mat['article'],reservation=mat['reservation'],quantity=mat['quantity'],unit_cents=unit,source=price_source.strip(),net_cents=mat['quantity']*unit,vat_percent=21))
  elif not no_material:
   quantity=v.get('material_quantity');unit=v.get('material_unit_cents');material_source=v.get('material_source','').strip()
   if type(quantity) is not int or not 0<quantity<=10000 or type(unit) is not int or not 0<unit<=100000000 or not material_source or len(material_source)>300:raise ValueError('Materiaal vereist aantal, positieve stukprijs en prijsbron')
   if consumed and quantity!=sum(r['quantity'] for r in consumed):raise ValueError('Aantal materiaal wijkt af van geregistreerd verbruik')
   lines.append(dict(description=j['materials'],quantity=quantity,unit_cents=unit,source=material_source,net_cents=quantity*unit,vat_percent=21))
  due=v.get('due','2026-11-09')
  if not isinstance(due,str) or len(due)!=10:raise ValueError('Vul vervaldatum YYYY-MM-DD in')
  date.fromisoformat(due)
  net=sum(line['net_cents'] for line in lines);vat=cents(Decimal(net)*Decimal('0.21'))
  j['sales_invoice']=dict(id='CF'+job[1:],status='concept',lines=lines,net_cents=net,vat_cents=vat,total_cents=net+vat,paid_cents=0,due=due)
 elif a in {'invoice_hours_apply','invoice_hours_reason'}:
  if not inv or inv['status']!='concept':raise ValueError('Alleen concept kan worden aangepast')
  check=invoice_control(s,job)
  if check['hours_total'] is None or check['billed_hours'] is None:raise ValueError('Bezoekuren of arbeidsregel onbekend; eerst controleren')
  before=check['signature']
  if a=='invoice_hours_apply':
   line=inv['lines'][0]
   if type(line.get('unit_cents')) is not int or line.get('vat_percent')!=21:raise ValueError('Controleer tarief en btw eerst')
   line['quantity']=check['hours_total'];line['net_cents']=cents(Decimal(str(line['quantity']))*line['unit_cents'])
   inv['net_cents']=sum(l['net_cents'] for l in inv['lines']);inv['vat_cents']=cents(Decimal(inv['net_cents'])*Decimal('0.21'));inv['total_cents']=inv['net_cents']+inv['vat_cents']
   reason='Geregistreerde bezoekuren expliciet overgenomen'
  else:
   if check['difference']<=0:raise ValueError('Alleen niet-gefactureerde uren kunnen worden verantwoord')
   reason=text_value(v,'reason',1000)
  inv['hours_resolution']=dict(signature=invoice_control(s,job)['signature'],reason=reason,action=a,role=role,date=date.today().isoformat())
  inv.setdefault('hours_audit',[]).append(dict(inv['hours_resolution'],before=before))
 elif a=='invoice_due':
  if not inv or inv['status']!='concept':raise ValueError('Alleen concept heeft een wijzigbare vervaldatum')
  try:date.fromisoformat(v.get('due',''))
  except (ValueError,TypeError):raise ValueError('Kies een geldige vervaldatum met de datumkiezer')
  inv['due']=v['due']
 elif a=='invoice_final':
  if not inv or inv['status']!='concept' or v.get('confirmed') is not True:raise ValueError('Controleer concept en bevestig regels/btw')
  if not inv.get('due'):raise ValueError('Kies eerst een vervaldatum voor het bestaande concept')
  if job=='W105' and not s.get('reviewed'):raise ValueError('Controleer eerst concept CF105')
  control=invoice_control(s,job)
  if control['blocked']:raise ValueError(control['message'])
  inv['status']='definitief';inv['issued_date']=date.today().isoformat();j['status']='gefactureerd'
 elif a=='invoice_send':
  if not inv or inv['status']!='definitief':raise ValueError('Maak eerst definitief')
  inv['status']='verstuurd (gesimuleerd)'
 elif a=='payment':
  amount=v.get('cents')
  if not inv or inv['status']!='verstuurd (gesimuleerd)':raise ValueError('Eerst fictief versturen')
  if type(amount) is not int or not 0<amount<=inv['total_cents']-inv['paid_cents']:raise ValueError('Bedrag moet positief en maximaal het open saldo zijn')
  inv['paid_cents']+=amount
  inv.setdefault('payments',[]).append(dict(cents=amount,date=date.today().isoformat(),simulated=True))
  if inv['paid_cents']==inv['total_cents']:j['status']='betaald (fictief)'

OPS={'part_purchase','part_ordered','part_confirm','part_receive','part_cancel','customer_followup','followup_plan','waiting_part_clear','timeblock_link','waiting_part','timeblock','timeblock_remove','worktime','invoice_followup','intake','plan','stock_receive','reserve','stock_use','purchase','purchase_receive','key_authorize','key_revoke','key_issue','installation','communication','warranty','warranty_decide','sale','quote_new'}
def text(v,key,limit=1000):
 value=v.get(key)
 if not isinstance(value,str) or not value.strip() or len(value)>limit:raise ValueError('Vul '+key+' in (max '+str(limit)+' tekens)')
 return value.strip()
def positive(v,key):
 n=v.get(key)
 if type(n) is not int or not 0<n<=100000000:raise ValueError(key+' moet een positief geheel getal zijn')
 return n
def operate(s,v):
 a=v['action'];role=v['role']
 allowed={'part_purchase':{'Eigenaar','Lina'},'part_ordered':{'Eigenaar','Lina'},'part_confirm':{'Eigenaar','Lina'},'part_receive':{'Eigenaar','Lina'},'part_cancel':{'Eigenaar','Lina'},'customer_followup':{'Eigenaar','Lina'},'followup_plan':{'Eigenaar','Lina'},'waiting_part_clear':{'Eigenaar','Lina','Bram'},'timeblock_link':{'Eigenaar','Lina'},'waiting_part':{'Eigenaar','Lina','Bram'},'timeblock':{'Eigenaar','Lina'},'timeblock_remove':{'Eigenaar','Lina'},'worktime':{'Eigenaar','Lina'},'invoice_followup':{'Administratie','Eigenaar'},'quote_new':{'Lina','Eigenaar'},'intake':{'Lina','Eigenaar'},'plan':{'Lina','Eigenaar'},'stock_receive':{'Lina','Eigenaar'},'purchase':{'Lina','Eigenaar'},'purchase_receive':{'Lina','Eigenaar'},'reserve':{'Lina','Eigenaar'},'stock_use':{'Bram','Eigenaar'},'key_authorize':{'Eigenaar'},'key_revoke':{'Eigenaar'},'key_issue':{'Lina','Eigenaar'},'installation':{'Bram','Eigenaar'},'communication':{'Lina','Eigenaar','Administratie'},'warranty':{'Lina','Eigenaar'},'warranty_decide':{'Eigenaar'},'sale':{'Lina','Eigenaar'}}
 if role not in allowed[a]:raise ValueError('Deze demorol mag deze handeling niet uitvoeren')
 ops=s.setdefault('operations',dict(orders={},stock={},purchases={},reservations={},authorizations={},events=[],sales={}))
 def add_event(kind,**kw):ops['events'].append(dict(id='E'+str(len(ops['events'])+1),kind=kind,role=role,date=date.today().isoformat(),**kw))
 def order():
  ident=text(v,'order',80)
  if ident not in {'W104','W105','W106'} and ident not in ops['orders']:raise ValueError('Onbekende werkorder')
  return ident
 def stock_key():return text(v,'part',100)+' @ '+text(v,'location',80)
 def free(key):return ops['stock'].get(key,0)-sum(r['quantity'] for r in ops['reservations'].values() if r['key']==key and r['status']=='gereserveerd')
 if a in {'part_purchase','part_ordered','part_confirm','part_receive','part_cancel','waiting_part_clear','customer_followup'}:
  ident=order();j=s.setdefault('jobs',{}).setdefault(ident,{});w=j.get('waiting_part')
  if not w:raise ValueError('Geen onderdeelbehoefte geregistreerd')
  status=w.get('status','behoefte geregistreerd');purchase=ops['purchases'].get(w.get('purchase_id'))
  if a=='customer_followup':
   owner=text(v,'responsible',80)
   if owner not in {'Eigenaar','Lina','Bram','Noor','Administratie'}:raise ValueError('Kies verantwoordelijke')
   day=text(v,'followup_date',10);date.fromisoformat(day);state=text(v,'contact_status',80)
   if state not in {'concept','opvolging gepland','handmatig afgehandeld'}:raise ValueError('Kies opvolgstatus')
   if status=='ontvangen' and 'wachten op' in text(v,'message').lower():raise ValueError('Verouderd concept: onderdeel is ontvangen; beoordeel de klanttekst opnieuw')
   j['customer_followup']=dict(responsible=owner,date=day,message=text(v,'message'),status=state,sent=False,part_status=status,review_required=False,appointment=j.get('followup_planning',{}).get('appointment'))
  elif a in {'part_cancel','waiting_part_clear'}:
   if status in {'ontvangen','geannuleerd'}:raise ValueError('Behoefte al afgesloten')
   w['status']='geannuleerd'
   if purchase:purchase['status']='geannuleerd'
  elif a=='part_purchase':
   if status!='behoefte geregistreerd' or purchase:raise ValueError('Inkooporder bestaat al of behoefte afgesloten')
   pid='I'+str(len(ops['purchases'])+1)
   purchase=dict(id=pid,order=ident,part=w['part'],supplier=w['supplier'],quantity=positive(v,'quantity'),location=text(v,'location',80),status='inkooporder aangemaakt')
   ops['purchases'][pid]=purchase;w.update(purchase_id=pid,status=purchase['status'])
  else:
   expected={'part_ordered':{'inkooporder aangemaakt'},'part_confirm':{'besteld'},'part_receive':{'besteld','bevestigd'}}[a]
   if not purchase or status not in expected:raise ValueError('Ongeldige inkoopstap of al ontvangen')
   if a=='part_confirm':
    delivery=text(v,'expected_delivery',10);date.fromisoformat(delivery);w['expected_delivery']=delivery
   if a=='part_receive':
    key=purchase['part']+' @ '+purchase['location'];ops['stock'][key]=ops['stock'].get(key,0)+purchase['quantity'];w['received_date']=date.today().isoformat();j['followup_required']=True
   w['status']={'part_ordered':'besteld','part_confirm':'bevestigd','part_receive':'ontvangen'}[a];purchase['status']=w['status']
  if a!='customer_followup' and j.get('customer_followup'):
   j['customer_followup']['review_required']=True
  add_event(a,order=ident,part=w['part'],status=w.get('status','behoefte geregistreerd'))
 elif a=='timeblock_link':
  ident=text(v,'block_id',80);block=ops.get('timeblocks',{}).get(ident);linked=order()
  if not block or block['kind']!='reistijd':raise ValueError('Kies een bestaand reisblok')
  appointment=next((b for b in bookings(s,block['day']) if b['id']==linked and not b.get('kind')),None)
  if not appointment or appointment['employee']!=block['employee']:raise ValueError('Kies afspraak van dezelfde monteur en dag')
  block['order']=linked;add_event(a,block_id=ident,order=linked)
 elif a=='waiting_part':
  ident=order();j=s.setdefault('jobs',{}).setdefault(ident,{})
  if j.get('completed'):raise ValueError('Gereedgemeld werk niet op onderdeel laten wachten')
  part=text(v,'part',200);supplier=text(v,'supplier',200);responsible=text(v,'responsible',80)
  if responsible not in {'Eigenaar','Lina','Bram','Administratie','Noor'}:raise ValueError('Kies een verantwoordelijke')
  followup=text(v,'followup_date',10);date.fromisoformat(followup)
  delivery=v.get('expected_delivery','')
  if delivery:date.fromisoformat(delivery)
  old=j.get('waiting_part',{})
  if old and old.get('status','behoefte geregistreerd') not in {'geannuleerd'}:raise ValueError('Bestaande behoefte eerst afhandelen; geen dubbele behoefte')
  if not j.get('diagnosis_visit'):
   original=j.get('planning') or ops['orders'].get(ident,{})
   j['diagnosis_visit']={k:original.get(k) for k in ('appointment','employee','duration_minutes')}
  j['followup_required']=True
  j['waiting_part']=dict(status='behoefte geregistreerd',part=part,supplier=supplier,responsible=responsible,followup_date=followup,expected_delivery=delivery or None)
  j.update(status='wachten op onderdeel',responsible=responsible);add_event(a,order=ident,part=part)
 elif a=='timeblock_remove':
  ident=text(v,'block_id',80)
  if ident not in ops.get('timeblocks',{}):raise ValueError('Onbekend bezet blok')
  del ops['timeblocks'][ident];add_event(a,block_id=ident)
 elif a=='timeblock':
  from datetime import datetime
  day=text(v,'day',10);date.fromisoformat(day);employee=text(v,'employee',80)
  kind=text(v,'kind',30);start=text(v,'start',5);end=text(v,'end',5)
  if employee not in {'Bram','Lina','Noor'} or kind not in {'pauze','reistijd','afwezig'}:raise ValueError('Kies monteur en soort blok')
  datetime.strptime(start,'%H:%M');datetime.strptime(end,'%H:%M')
  if start>=end:raise ValueError('Eindtijd moet na begintijd liggen; vul werkelijke reistijd zelf in')
  at=day+'T'+start;finish=day+'T'+end
  for item in bookings(s,day):
   if item['employee']!=employee:continue
   if not item.get('end'):raise ValueError('Klusduur ontbreekt bij '+item['id'])
   if at<item['end'] and finish>item['appointment']:raise ValueError('Blok overlapt '+item['id'])
  linked=None
  if kind=='reistijd':
   linked=order();appointment=next((b for b in bookings(s,day) if b['id']==linked and not b.get('kind')),None)
   if not appointment or appointment['employee']!=employee:raise ValueError('Koppel reistijd aan een afspraak van dezelfde monteur en dag')
  blocks=ops.setdefault('timeblocks',{});ident='B'+str(max([0]+[int(k[1:]) for k in blocks])+1)
  blocks[ident]=dict(id=ident,day=day,employee=employee,kind=kind,start=start,end=end,order=linked);add_event(a,block_id=ident,day=day,employee=employee,kind_label=kind,start=start,end=end)
 elif a=='worktime':
  from datetime import datetime
  day=text(v,'day',10);date.fromisoformat(day);employee=text(v,'employee',80)
  if employee not in {'Bram','Lina','Noor'}:raise ValueError('Onbekende medewerker')
  start=text(v,'start',5);end=text(v,'end',5)
  datetime.strptime(start,'%H:%M');datetime.strptime(end,'%H:%M')
  if start>=end:raise ValueError('Eindtijd moet na begintijd liggen')
  for item in bookings(s,day):
   if item['employee']==employee and not item.get('kind') and (item['appointment'][11:]<start or (item.get('end') or item['appointment'])[11:]>end):raise ValueError('Werktijden sluiten bestaande afspraak uit; pas eerst planning aan')
  ops.setdefault('worktimes',{}).setdefault(day,{})[employee]=dict(start=start,end=end);add_event(a,employee=employee,day=day,start=start,end=end)
 elif a=='invoice_followup':
  from data import INVOICES
  ident=text(v,'invoice',80);inv=next((i for i in INVOICES if i['id']==ident),None)
  inv=inv or next((j['sales_invoice'] for j in s.get('jobs',{}).values() if j.get('sales_invoice',{}).get('id')==ident),None)
  if not inv or inv.get('status')=='concept' or inv['due']>=date.today().isoformat() or inv['net_cents']+inv['vat_cents']<=inv['paid_cents']:raise ValueError('Kies een vervallen factuur met open saldo')
  at=text(v,'next_date',10);date.fromisoformat(at)
  if at<date.today().isoformat():raise ValueError('Volgende actie mag niet in het verleden liggen')
  responsible=v.get('responsible') or ops.get('invoice_followups',{}).get(ident,{}).get('responsible') or 'Administratie'
  if responsible not in {'Eigenaar','Administratie','Bram','Lina','Noor'}:raise ValueError('Kies een bestaande verantwoordelijke')
  note=text(v,'note');ops.setdefault('invoice_followups',{})[ident]=dict(note=note,next_date=at,responsible=responsible,status='opvolging gepland — niets verzonden');add_event(a,invoice=ident,next_date=at,note=note,responsible=responsible)
 elif a in {'intake','quote_new'}:
  ident='W'+str(max([106]+[int(k[1:]) for k in ops['orders'] if k[1:].isdigit()])+1);customer=text(v,'customer',200);scope=text(v,'scope');priority=v.get('priority')
  if priority not in {'normaal','spoed'}:raise ValueError('Kies normaal of spoed')
  details={key:text(v,key,300) for key in ('address','phone','access')} if a=='intake' else {}
  ops['orders'][ident]=dict(**details,agreement_required=a=='intake',id=ident,customer=customer,scope=scope,priority=priority,status='intake',contact=text(v,'contact',200));add_event(a,order=ident)
  if a=='quote_new':
   ops['orders'][ident]['kind']='offerte'
   s.setdefault('jobs',{})[ident]=dict(status='offerteconcept — prijs ontbreekt',responsible=role,quote=dict(id='O'+ident[1:],scope=scope))
 elif a in {'plan','followup_plan'}:
  ident=order();j=s.setdefault('jobs',{}).setdefault(ident,{})
  if j.get('completed') or (ident=='W105' and s.get('registered')):raise ValueError('Gereedgemeld werk niet herplannen')
  if (ident=='W106' or ops['orders'].get(ident,{}).get('kind')=='offerte') and not j.get('accepted'):raise ValueError('Leg eerst offerteakkoord vast')
  followup=a=='followup_plan'
  if followup and not j.get('diagnosis_visit'):
   original=j.get('planning') or ops['orders'].get(ident,{})
   j['diagnosis_visit']={k:original.get(k) for k in ('appointment','employee','duration_minutes')}
  if j.get('waiting_part') and not followup:raise ValueError('Diagnosebezoek behouden; gebruik aparte vervolgplanning')
  if followup and j.get('waiting_part',{}).get('status')!='ontvangen':raise ValueError('Registreer eerst onderdeelontvangst')
  at=text(v,'appointment',16);from datetime import datetime
  datetime.strptime(at,'%Y-%m-%dT%H:%M');employee=text(v,'employee',80)
  if employee not in {'Bram','Lina','Noor'}:raise ValueError('Kies Bram, Lina of Noor')
  duration=v.get('duration_minutes')
  if type(duration) is not int or not 1<=duration<=720:raise ValueError('Vul klusduur in minuten in (1–720)')
  from datetime import timedelta
  dt=datetime.fromisoformat(at);finish=dt+timedelta(minutes=duration)
  shift=ops.get('worktimes',{}).get(at[:10],{}).get(employee)
  if not shift:raise ValueError('Leg eerst werktijden vast voor deze medewerker en dag')
  if finish.date()!=dt.date() or at[11:]<shift['start'] or finish.strftime('%H:%M')>shift['end']:raise ValueError('Afspraak valt buiten werktijden')
  for item in bookings(s,at[:10]):
   if (item['id']==ident and not followup) or item['id']==ident+'-vervolg' or item['employee']!=employee:continue
   if not item.get('end'):raise ValueError('Klusduur ontbreekt bij '+item['id']+'; vul die eerst aan')
   if at<item['end'] and finish.isoformat(timespec='minutes')>item['appointment']:raise ValueError('Afspraak overlapt '+item['id'])
  linked=[b for b in ops.get('timeblocks',{}).values() if b.get('order')==ident]
  if not followup and any(b['day']!=at[:10] or b['employee']!=employee for b in linked):raise ValueError('Pas gekoppelde reistijd eerst aan voordat dag of monteur wijzigt')
  planning=dict(appointment=at,employee=employee,duration_minutes=duration)
  if followup:
   j['followup_planning']=planning;j['followup_required']=False
   if j.get('customer_followup'):j['customer_followup']['review_required']=True
   add_event(a,order=ident,**planning);return s
  if ident in ops['orders']:ops['orders'][ident].update(**planning,status='gepland')
  s.setdefault('jobs',{}).setdefault(ident,{}).update(planning=planning,status='gepland',responsible=employee)
  if ident=='W105':
   if s.get('registered'):raise ValueError('Geregistreerd W105 niet herplannen')
   if at<s['delivery_at']:raise ValueError('Plan W105 na levering')
   s['appointment']=at;s['contact']='opnieuw bevestigen nodig'
  add_event(a,order=ident,**planning)
 elif a=='purchase':
  ident='I'+str(len(ops['purchases'])+1);ops['purchases'][ident]=dict(id=ident,part=text(v,'part',100),quantity=positive(v,'quantity'),supplier=text(v,'supplier',200),location=text(v,'location',80),status='inkooporder aangemaakt');add_event(a,purchase=ident)
 elif a=='purchase_receive':
  ident=text(v,'purchase',80);item=ops['purchases'].get(ident)
  if not item or item.get('order') or item['status'] not in {'inkooporder aangemaakt','besteld (fictief)','besteld','bevestigd'}:raise ValueError('Kies een open inkoopnummer')
  key=item['part']+' @ '+item['location'];ops['stock'][key]=ops['stock'].get(key,0)+item['quantity'];item['status']='ontvangen';add_event(a,purchase=ident)
 elif a=='stock_receive':
  key=stock_key();qty=positive(v,'quantity');source=text(v,'source',300);ops['stock'][key]=ops['stock'].get(key,0)+qty;add_event(a,key=key,quantity=qty,source=source)
 elif a=='reserve':
  ident=order();key=stock_key();qty=positive(v,'quantity')
  if s.get('jobs',{}).get(ident,{}).get('completed'):raise ValueError('Gereedgemeld dossier: geen nieuwe reservering')
  w=s.get('jobs',{}).get(ident,{}).get('waiting_part',{})
  if any(r['order']==ident and r['key']==key and r['status'] in {'gereserveerd','verbruikt'} for r in ops['reservations'].values()):raise ValueError('Artikel is al gereserveerd of verbruikt voor deze werkorder; geen duplicaat')
  if w.get('status')=='ontvangen' and key.split(' @ ')[0]==w.get('part') and any(r['order']==ident and r['key']==key and r['status'] in {'gereserveerd','verbruikt'} for r in ops['reservations'].values()):raise ValueError('Onderdeel is al gereserveerd of verbruikt voor deze klus')
  if free(key)<qty:raise ValueError('Onvoldoende vrije voorraad op deze locatie')
  rid='R'+str(len(ops['reservations'])+1);ops['reservations'][rid]=dict(id=rid,order=ident,key=key,quantity=qty,status='gereserveerd');add_event(a,reservation=rid,order=ident)
  if v.get('unit_cents') is not None:
   unit=positive(v,'unit_cents');price_source=text(v,'price_source',300)
   ops['reservations'][rid].update(unit_cents=unit,price_source=price_source)
 elif a=='stock_use':
  rid=text(v,'reservation',80);r=ops['reservations'].get(rid)
  if not r or r['status']!='gereserveerd':raise ValueError('Kies een open reservering')
  if s.get('jobs',{}).get(r['order'],{}).get('sales_invoice'):raise ValueError('Concept bestaat al; geen materiaal meer wijzigen')
  ops['stock'][r['key']]-=r['quantity'];r['status']='verbruikt';add_event(a,order=r['order'],reservation=rid,key=r['key'],quantity=r['quantity'])
 elif a=='key_authorize':
  ident='A'+str(len(ops['authorizations'])+1);ops['authorizations'][ident]=dict(id=ident,order=order(),plan=text(v,'plan',200),holder=text(v,'holder',200),scope=text(v,'scope'),proof=text(v,'proof',300),limit=positive(v,'quantity'),issued=0,active=True);add_event(a,authorization=ident)
 elif a=='key_revoke':
  ident=text(v,'authorization',80);auth=ops['authorizations'].get(ident)
  if not auth or not auth.get('active',True):raise ValueError('Kies een actieve autorisatie')
  auth['active']=False;add_event(a,authorization=ident,reason=text(v,'reason',300))
 elif a=='key_issue':
  ident=text(v,'authorization',80);auth=ops['authorizations'].get(ident)
  if not auth or not auth.get('active',True):raise ValueError('Actieve eigenaarautorisatie vereist')
  quantity=positive(v,'quantity')
  if quantity>auth.get('limit',0)-auth.get('issued',0):raise ValueError('Aantal overschrijdt eigenaarautorisatie')
  auth['issued']=auth.get('issued',0)+quantity;add_event(a,order=auth['order'],authorization=ident,quantity=quantity,recipient=auth['holder'])
 elif a=='installation':add_event(a,order=order(),device=text(v,'device',200),location=text(v,'location',80),findings=text(v,'findings'))
 elif a=='communication':add_event(a,order=order(),channel=text(v,'channel',80),message=text(v,'message'),status='intern concept — niet verzonden')
 elif a=='warranty':add_event(a,order=order(),proof=text(v,'proof',300),findings=text(v,'findings'),status='garantiebeoordeling open')
 elif a=='warranty_decide':
  ident=text(v,'claim',80);claim=next((event for event in ops['events'] if event.get('id')==ident and event['kind']=='warranty'),None)
  if not claim or claim['status']!='garantiebeoordeling open':raise ValueError('Kies een open garantiemelding E…')
  decision=v.get('decision')
  if decision not in {'toegekend','afgewezen'}:raise ValueError('Kies toegekend of afgewezen')
  findings=text(v,'findings');claim['status']='garantie '+decision;add_event(a,order=claim['order'],claim=ident,decision=decision,findings=findings)
 elif a=='sale':
  key=stock_key();qty=positive(v,'quantity');price=positive(v,'unit_cents');source=text(v,'source',300)
  if free(key)<qty:raise ValueError('Onvoldoende vrije winkelvoorraad')
  net=qty*price;vat=cents(Decimal(net)*Decimal('.21'));ident='B'+str(len(ops['sales'])+1)
  ops['sales'][ident]=dict(id=ident,key=key,quantity=qty,unit_cents=price,source=source,net_cents=net,vat_cents=vat,total_cents=net+vat,status='fictieve contante verkoop',date=date.today().isoformat(),paid_cents=net+vat)
  ops['stock'][key]-=qty;add_event(a,sale=ident)


def text_value(v,key,limit):return text(v,key,limit)
def quote_lines(lines):
 if not isinstance(lines,list) or not 1<=len(lines)<=10:raise ValueError('Gebruik 1–10 offerteregels')
 result=[]
 for line in lines:
  if not isinstance(line,dict):raise ValueError('Ongeldige offerteregel')
  quantity=positive(line,'quantity');unit=positive(line,'unit_cents')
  if quantity*unit>100000000:raise ValueError('Offerteregel te groot')
  result.append(dict(description=text(line,'description',300),quantity=quantity,unit_cents=unit,source=text(line,'source',300),net_cents=quantity*unit,vat_percent=21))
 return result

def bookings(s,day):
 from datetime import datetime,timedelta
 from data import ORDERS
 result=[];ops=s.get('operations',{});jobs=s.get('jobs',{})
 for o in ORDERS+list(ops.get('orders',{}).values()):
  ident=o['id'];j=jobs.get(ident,{})
  if j.get('cancelled') or o.get('status')=='afgerond' or j.get('completed') or (ident=='W105' and s.get('registered')):continue
  if (ident=='W106' or o.get('kind')=='offerte') and not j.get('accepted'):continue
  plan=j.get('planning') or o
  at=plan.get('appointment')
  if ident=='W105':at=s['appointment']
  if not at and o.get('status')=='afgerond':at='2026-10-26T'+o['time']
  if not at or not at.startswith(day):continue
  duration=plan.get('duration_minutes');end=(datetime.fromisoformat(at)+timedelta(minutes=duration)).isoformat(timespec='minutes') if duration else None
  result.append(dict(id=ident,appointment=at,end=end,duration_minutes=duration,employee=plan.get('employee',o.get('employee','Niet toegewezen')),visit_kind='diagnosebezoek' if j.get('waiting_part') else None))
 for ident,j in jobs.items():
  plan=j.get('followup_planning')
  if plan and not j.get('completed') and not j.get('cancelled') and plan['appointment'].startswith(day):
   at=plan['appointment'];result.append(dict(id=ident+'-vervolg',order=ident,appointment=at,end=(datetime.fromisoformat(at)+timedelta(minutes=plan['duration_minutes'])).isoformat(timespec='minutes'),duration_minutes=plan['duration_minutes'],employee=plan['employee'],visit_kind='vervolgbezoek'))
 for block in ops.get('timeblocks',{}).values():
  if block['day']==day:result.append(dict(id=block['id'],appointment=day+'T'+block['start'],end=day+'T'+block['end'],duration_minutes=None,employee=block['employee'],kind=block['kind'],order=block.get('order')))
 return result

def availability(s,day):
 from datetime import datetime,timedelta
 result=[]
 for employee in ('Bram','Lina','Noor'):
  shift=s.get('operations',{}).get('worktimes',{}).get(day,{}).get(employee)
  items=[b for b in bookings(s,day) if b['employee']==employee]
  unknown=[b['id'] for b in items if not b['end']]
  free=[]
  if shift:
   cursor=day+'T'+shift['start'];end=day+'T'+shift['end']
   for b in sorted((b for b in items if b['end']),key=lambda b:b['appointment']):
    if b['appointment']>cursor:free.append(dict(start=cursor,end=min(end,b['appointment'])))
    cursor=max(cursor,b['end'])
   if cursor<end:free.append(dict(start=cursor,end=end))
   free=[i for i in free if i['start']<i['end']]
  result.append(dict(employee=employee,shift=shift,bookings=items,unknown_duration=unknown,free=free if not unknown else [],availability_known=bool(shift) and not unknown))
 return result


def job_status(s,ident,fallback):
 j=s.get('jobs',{}).get(ident,{})
 if j.get('cancelled'):return 'geannuleerd'
 if j.get('sales_invoice'):
  from improvements import dossier_state
  return dossier_state(s,ident)['label']
 if j.get('completed'):return j.get('status',fallback)
 if j.get('waiting_part'):
  state=j['waiting_part'].get('status','behoefte geregistreerd')
  if state not in {'geannuleerd','ontvangen'}:return 'wachten op onderdeel'
  if state=='ontvangen':return 'vervolg gepland' if j.get('followup_planning') else 'onderdeel ontvangen — vervolg plannen'
 if ident=='W105':return fallback
 if j.get('findings') or j.get('materials') or j.get('hours'):return 'in uitvoering — concept opgeslagen'
 op=s.get('operations',{}).get('orders',{}).get(ident,{})
 if (j.get('planning') or op).get('appointment') and (ident!='W106' or j.get('accepted')):return 'gepland'
 return j.get('status',fallback)


def customer_followup_view(j, customer):
 w=j.get('waiting_part',{});c=dict(j.get('customer_followup') or {})
 current=w.get('status')
 plan=j.get('followup_planning')
 stale=bool(c) and (bool(plan and c.get('appointment')!=plan['appointment']) or c.get('review_required',False) or (c.get('part_status') is not None and c['part_status']!=current) or (current=='ontvangen' and 'wachten op' in c.get('message','').lower()))
 c['review_required']=stale
 if stale:c['status']='herbeoordeling nodig'
 if j.get('completed'):
  c.update(review_required=bool(c.get('message')) and c.get('status')!='handmatig afgehandeld',status='handmatig afgehandeld' if c.get('status')=='handmatig afgehandeld' else 'te beoordelen / af te sluiten',suggested_message='',active_followup=False)
  return c
 c['suggested_message']=('Beste '+customer+', het onderdeel voor uw reparatie is ontvangen. Wij nemen contact met u op om een vervolgafspraak af te spreken.' if current=='ontvangen' else 'Beste '+customer+', wij wachten op het onderdeel voor uw reparatie. Zodra het binnen is, spreken wij het vervolg met u af.')
 if plan:
  from workflow import dutch_date
  c['suggested_message']='Beste '+customer+', uw vervolgafspraak staat gepland op '+dutch_date(plan['appointment'])+'.'
 return c

def invoice_proposal(s,job):
 j=s.get('jobs',{}).get(job,{})
 visits=j.get('visit_hours')
 hours=[]
 if j.get('diagnosis_visit'):
  for key,label in [('diagnosis','Diagnose'),('followup','Vervolg')]:
   if key=='followup' and not j.get('followup_planning'):continue
   hours.append(dict(visit=key,label=label,hours=(visits or {}).get(key),source=job+' · '+label+'bezoek'))
 else:hours=[dict(visit='work',label='Werk',hours=j.get('hours'),source=job+' · werkregistratie')]
 known=all(x['hours'] is not None for x in hours)
 materials=[]
 inv=j.get('sales_invoice') or {}
 for rid,res in s.get('operations',{}).get('reservations',{}).items():
  if res['order']!=job or res['status']!='verbruikt':continue
  part=res['key'].split(' @ ')[0]
  matching=[(idx,line) for idx,line in enumerate(inv.get('lines',[])) if idx>0 and (line.get('reservation')==rid or (not line.get('reservation') and (rid in line.get('source','') or part.lower() in line.get('description','').lower())))]
  match=matching[0] if len(matching)==1 else None
  materials.append(dict(reservation=rid,article=part,quantity=res['quantity'],source=job+' · verbruik '+rid,review_required=True,existing_line=match[0] if match else None,unit_cents=match[1].get('unit_cents') if match else res.get('unit_cents'),price_source=match[1].get('source') if match else res.get('price_source')))
 return dict(visits=hours,hours_total=sum(x['hours'] for x in hours) if known else None,materials=materials,existing_invoice=inv.get('id'))


def invoice_control(s,job):
 import json
 j=s.get('jobs',{}).get(job,{});inv=j.get('sales_invoice') or {};proposal=invoice_proposal(s,job)
 lines=inv.get('lines',[]);labor=[l for l in lines if l.get('description','').lower().startswith('arbeid')]
 billed=labor[0].get('quantity') if len(labor)==1 and lines[0] is labor[0] else None
 total=proposal['hours_total'];difference=round(total-billed,6) if total is not None and billed is not None else None
 signature=json.dumps(dict(visits=proposal['visits'],lines=lines),sort_keys=True)
 resolved=inv.get('hours_resolution',{}).get('signature')==signature and bool(inv.get('hours_resolution',{}).get('reason'))
 blocked=total is None or billed is None or (difference!=0 and not resolved)
 message='Bezoekuren of arbeidsregel onbekend; controle nodig' if difference is None else f'{total:g} uur geregistreerd, {billed:g} uur op factuur, verschil {difference:g} uur (€{abs(cents(Decimal(str(difference))*labor[0]["unit_cents"]))/100:g} excl btw bij €{labor[0]["unit_cents"]/100:g}/u)'
 material_block=False;seen=set()
 for mat in proposal['materials']:
  idx=mat['existing_line']
  if idx is None or idx in seen or lines[idx]['quantity']!=mat['quantity']:material_block=True
  seen.add(idx)
 if material_block:message+=' · Materiaalverbruik en factuurregels controleren; ontbrekende of dubbele koppeling'
 billing=billing_control(s,job)
 if billing['required']:
  message+=' · '+billing['message']
  if j.get('billing',{}).get('mode') in {'fixed','extra'}:blocked=False;material_block=False;message=billing['message']+' · Uren en verbruik blijven in opdrachtdossier; afrekening volgens prijsafspraak'
 return dict(billing=billing,hours_total=total,billed_hours=billed,difference=difference,signature=signature,blocked=(blocked or material_block or billing['blocked']) if not inv.get('replacement') else False,message=message.replace('1.5','1,5').replace('0.5','0,5'),resolved=resolved)


def registered_material_complete(s,job):
 rows=[r for r in s.get('operations',{}).get('reservations',{}).values() if r['order']==job]
 used=[r for r in rows if r['status']=='verbruikt']
 return bool(used) and not any(r['status']=='gereserveerd' for r in rows) and all(r.get('key') and r.get('quantity',0)>0 and type(r.get('unit_cents')) is int and r['unit_cents']>0 and r.get('price_source','').strip() for r in used)

def labor_rate_reference(s,job):
 # Only the same customer's recorded labor agreement is a candidate.
 from data import ORDERS
 customers={o['id']:o['customer'] for o in ORDERS}
 customers.update({k:o['customer'] for k,o in s.get('operations',{}).get('orders',{}).items()})
 customer=customers.get(job)
 for key in [customer,'*']:
  if key in s.get('tariffs',{}):return dict(s['tariffs'][key],reference='Expliciet beheerd tarief · '+key)
 for ident,j in reversed(list(s.get('jobs',{}).items())):
  if ident==job or not customer or customers.get(ident)!=customer:continue
  inv=j.get('sales_invoice',{})
  for line in inv.get('lines',[]):
   if line.get('description','').lower().startswith('arbeid') and type(line.get('unit_cents')) is int and line['unit_cents']>0 and line.get('source'):
    return dict(unit_cents=line['unit_cents'],source=line['source'],reference=inv['id']+' · '+ident+' · '+customer)
 return None


BILLING_MODES={'fixed':'Vaste offerteprijs','actual':'Werkelijke uren en materiaal / nacalculatie','extra':'Offerteprijs plus afzonderlijk goedgekeurd meerwerk'}
def billing_control(s,job):
 import json,hashlib
 j=s.get('jobs',{}).get(job,{});inv=j.get('sales_invoice') or {};b=j.get('billing',{});q=j.get('order') or j.get('quote') or {}
 required=bool(j.get('accepted'));quote=q.get('net_cents');net=inv.get('net_cents');mode=b.get('mode');extra=b.get('extra_cents',0)
 signature=hashlib.sha256(json.dumps(dict(quote=q,billing=b,lines=inv.get('lines'),visits=invoice_proposal(s,job)['visits']),sort_keys=True).encode()).hexdigest()
 errors=[]
 if required:
  if mode not in BILLING_MODES:errors.append('Afrekenvorm ontbreekt')
  if type(quote) is not int:errors.append('Geaccepteerde offerteprijs ontbreekt')
  if not b.get('reason') or not b.get('approval'):errors.append('Reden en herleidbare klantafspraak / goedkeuring ontbreken')
  if mode=='extra' and (not b.get('extra_approval') or not b.get('extra_description') or type(extra) is not int or extra<=0):errors.append('Afzonderlijk goedgekeurd meerwerk ontbreekt')
  if mode in {'fixed','extra'}:
   expected=quote+(extra if mode=='extra' else 0) if type(quote) is int else None
   expected_lines=billing_lines(j) if expected is not None else []
   if net!=expected or inv.get('lines')!=expected_lines:errors.append('Concept wijkt af van prijsafspraak; pas concept expliciet toe')
  if mode=='actual' and net!=quote and inv.get('billing_resolution',{}).get('signature')!=signature:errors.append('Offerteafwijking vereist actuele reden en klantgoedkeuring')
 return dict(required=required,quote_cents=quote,mode=mode,mode_label=BILLING_MODES.get(mode,'Nog kiezen'),net_cents=net,difference_cents=(quote-net if type(quote) is int and type(net) is int else None),blocked=bool(errors),message=' · '.join(errors) or 'Afrekenafspraak en afwijking verantwoord',signature=signature)

def billing_lines(j):
 b=j['billing'];q=j.get('order') or j['quote'];amount=q['net_cents']
 lines=[dict(description='Vaste offerteprijs '+q.get('id',''),quantity=1,unit_cents=amount,net_cents=amount,source=q.get('source','')+' · '+b['approval'],vat_percent=21)]
 if b['mode']=='extra':
  amount=b['extra_cents'];lines.append(dict(description='Meerwerk: '+b['extra_description'],quantity=1,unit_cents=amount,net_cents=amount,source=b['extra_approval'],vat_percent=21))
 return lines

def billing_mutate(s,v):
 import copy
 from datetime import datetime,timezone
 if v['role'] not in {'Eigenaar','Administratie'}:raise ValueError('Prijsafspraken horen bij eigenaar / administratie')
 a=v['action'];j=s.get('jobs',{}).get(v.get('job'),{});inv=j.get('sales_invoice')
 stamp=dict(role=v['role'],at=datetime.now(timezone.utc).isoformat())
 if a=='tariff_save':
  key=text_value(v,'customer',300);rate=v.get('rate_cents');source=text_value(v,'source',300)
  if type(rate) is not int or not 0<rate<=1000000:raise ValueError('Expliciet positief uurtarief vereist')
  tariffs=s.setdefault('tariffs',{});before=copy.deepcopy(tariffs.get(key));tariffs[key]=dict(unit_cents=rate,source=source,**stamp)
  s.setdefault('tariff_history',[]).append(dict(customer=key,before=before,after=copy.deepcopy(tariffs[key]),**stamp));return
 if not j.get('accepted'):raise ValueError('Afrekenafspraak vereist geaccepteerde opdracht')
 if inv and inv['status']!='concept':raise ValueError('Alleen conceptafrekening aanpassen')
 before=copy.deepcopy(j.get('billing'))
 if a=='billing_save':
  mode=v.get('mode')
  if mode not in BILLING_MODES:raise ValueError('Kies expliciet een afrekenvorm')
  who=text(v,'approval_who',300);approved_on=text(v,'approval_date',10);date.fromisoformat(approved_on);reference=text(v,'approval_reference',300)
  b=dict(approval_who=who,approval_date=approved_on,approval_reference=reference,mode=mode,reason=text_value(v,'reason',1000),approval=who+' · '+approved_on+' · '+reference,**stamp)
  if mode=='extra':
   extra=v.get('extra_cents')
   if type(extra) is not int or not 0<extra<=100000000:raise ValueError('Expliciet positief meerwerkbedrag vereist')
   extra_who=text(v,'extra_who',300);extra_date=text(v,'extra_date',10);date.fromisoformat(extra_date);extra_reference=text(v,'extra_reference',300)
   b.update(extra_who=extra_who,extra_date=extra_date,extra_reference=extra_reference,extra_cents=extra,extra_description=text_value(v,'extra_description',1000),extra_approval=extra_who+' · '+extra_date+' · '+extra_reference)
  j['billing']=b
  j.setdefault('billing_history',[]).append(dict(before=before,after=copy.deepcopy(b),**stamp))
  # Saving the agreement never changes invoice lines or amounts.
 elif a=='billing_apply':
  if not inv or j.get('billing',{}).get('mode') not in {'fixed','extra'}:raise ValueError('Kies eerst vaste offerteprijs of goedgekeurd meerwerk')
  old=copy.deepcopy(inv);inv['lines']=billing_lines(j);net=sum(x['net_cents'] for x in inv['lines']);vat=cents(Decimal(net)*Decimal('.21'));inv.update(net_cents=net,vat_cents=vat,total_cents=net+vat)
  j.setdefault('billing_history',[]).append(dict(action=a,before_invoice=old,after_invoice=copy.deepcopy(inv),**stamp))
 if inv:
  inv['billing_resolution']=dict(signature=billing_control(s,v['job'])['signature'],reason=j['billing']['reason'],approval=j['billing']['approval'],**stamp)
  inv['billing']=copy.deepcopy(j['billing'])


def dossier_flow(s,job):
 j=s.get('jobs',{}).get(job,{})
 op=s.get('operations',{}).get('orders',{}).get(job,{})
 inv=j.get('sales_invoice') or {}
 def step(n,title,target,block=''):
  return dict(number=n,total=10,title=title,target=target,block=block,accounting='niet gekoppeld',simulated=True)
 if j.get('administrative_closed'):return step(10,'Administratief afgerond (demo)','done')
 if (op.get('kind')=='offerte' or job=='W106') and not j.get('accepted'):
  return step(1,'Offerte invullen en opslaan' if not j.get('quote',{}).get('net_cents') else 'Fictief klantakkoord vastleggen','quote')
 if op.get('agreement_required') and not j.get('direct_agreement') and not j.get('accepted'):return step(1,'Leg direct opdrachtakkoord vast','agreement')
 if not (j.get('planning') or op).get('appointment'):return step(2,'Plan deze opdracht','plan')
 if not j.get('completed'):
  waiting=j.get('waiting_part',{});status=waiting.get('status')
  if status=='behoefte geregistreerd':return step(3,'Maak de inkooporder voor het ontbrekende onderdeel','part_purchase')
  if status=='inkooporder aangemaakt':return step(3,'Registreer de fictieve bestelling','part_ordered')
  if status in {'besteld','bevestigd','gedeeltelijk ontvangen'}:return step(3,'Registreer de deelontvangst of restontvangst','purchase_partial','Levering nog niet volledig ontvangen')
  if status=='ontvangen' and not j.get('followup_planning'):return step(3,'Plan het vervolgbezoek','followup_plan')
  held=[r['id'] for r in s.get('operations',{}).get('reservations',{}).values() if r['order']==job and r['status']=='gereserveerd']
  return step(3,'Registreer uitvoering, uren en materiaal; meld gereed','execution',('Open reserveringen: '+', '.join(held)) if held else '')
 if j.get('customer_followup',{}).get('review_required'):return step(4,'Beoordeel oud klantconcept','customer_followup','Oud klantconcept nog open')
 if not inv:return step(5,'Controleer prijsafspraak en maak conceptfactuur','finance')
 if inv['status']=='concept':
  check=invoice_control(s,job)
  return step(6,'Controleer concept en maak definitief','finance',check['message'] if check['blocked'] else '')
 if inv['status']=='definitief':return step(7,'Registreer fictieve verzending','finance')
 from improvements import balance
 state=__import__('improvements').dossier_state(s,job)
 if state['financial_difference_cents']:return step(8,'Stem het financiële verschil af','reconcile','Betalingsregistraties wijken af van het ontvangen totaal')
 if balance(inv)['open_cents']<0:return step(8,'Registreer fictieve terugbetaling','refund')
 if balance(inv)['open_cents']>0:return step(8,'Registreer fictieve betaling','payment')
 if j.get('accounting',{}).get('state')=='error':return step(8,'Controleer de boekhoudafstemming','accounting',j['accounting'].get('reason','Controle en bewijsreferentie nodig'))
 return step(9,'Sluit dossier administratief af (demo)','close')
