"""Shared fictional W105 state. No integrations, invoices remain drafts."""
import json,os,tempfile,threading,copy,math,hashlib
from datetime import datetime,timezone
from pathlib import Path
FILE=Path.home()/'.local/state/server4-mobile-demo/workflow.json'
LOCK=threading.RLock()
ROLES={'Lina','Eigenaar','Bram','Administratie'}
def initial(revision=0):
 return dict(revision=revision,delivery_status='onbevestigd',delivery_at='2026-10-27T10:00',appointment='2026-10-26T16:00',contact='niet benaderd',hours=0,materials=0,registered=False,reviewed=False,history=[])
def load():
 try:return json.loads(FILE.read_text())
 except FileNotFoundError:return initial()
def dutch_date(value):
 dt=datetime.fromisoformat(value)
 months=['januari','februari','maart','april','mei','juni','juli','augustus','september','oktober','november','december']
 return f"{dt.day} {months[dt.month-1]}"+(f" om {dt:%H.%M} uur" if 'T' in value else '')
def view(s=None):
 with LOCK:
  s=copy.deepcopy(load() if s is None else s)
 net=round(s['hours']*6000)+s['materials']*15000;vat=(net*21+50)//100
 status='concept gecontroleerd' if s['reviewed'] else 'gereed voor administratie' if s['registered'] else 'klaar voor montage' if s['delivery_status']=='ontvangen' and s['appointment']>=s['delivery_at'] else 'herpland; wacht op levering' if s['appointment']>=s['delivery_at'] else 'levering bevestigd; herplan afspraak' if s['delivery_status']=='bevestigd' else 'geblokkeerd: planning vóór levering'
 todo={'Lina':'Bevestig verwachte levering; markeer daarna fictieve ontvangst.','Eigenaar':'Verzet afspraak ná levering; beoordeel concept en leg fictieve klantcontactstatus vast.','Bram':'Wacht op ontvangst en herplanning; registreer daarna uren en materiaal.','Administratie':'Wacht op monteursregistratie; controleer daarna automatisch gevuld concept CF105.'}
 if s['delivery_status']=='bevestigd':todo['Lina']='Markeer ontvangen zodra het onderdeel fictief binnen is.'
 if s['delivery_status']=='ontvangen':todo['Lina']='Levering ontvangen; geen verdere voorraadactie nodig.'
 if s['appointment']>=s['delivery_at']:todo['Eigenaar']='Controleer klantcontactstatus; conceptbericht wordt nooit verzonden.'
 if s['delivery_status']=='ontvangen' and s['appointment']>=s['delivery_at'] and s['contact']=='fictief akkoord':todo['Bram']='Vul werkelijk gebruikte demo-uren en materiaal in en sla op.'
 if s['registered']:todo['Bram']='Registratie opgeslagen; administratie gebruikt exact deze regels.';todo['Administratie']='Controleer concept CF105; geen definitieve factuur of boeking.'
 if s['reviewed']:todo['Administratie']='Concept gecontroleerd. Demo klaar; geen verzending of boeking.'
 if s['appointment']>=s['delivery_at'] and s['contact']=='fictief akkoord':todo['Eigenaar']='Afspraak en klantakkoord zijn vastgelegd. Geen persoonlijke actie open.'
 if s['registered']:todo['Bram']='Je bent klaar. De administratie controleert je registratie.'
 if s['reviewed']:
  todo={role:'Je bent klaar. W105 is afgerond; conceptfactuur CF105 is gecontroleerd.' for role in ROLES}
 from business import existing_w105,job_status,customer_followup_view,invoice_proposal,invoice_control,registered_material_complete,labor_rate_reference
 from business import dossier_flow
 from improvements import invoice as project_legacy
 from data import INVOICES
 for legacy in INVOICES:project_legacy(s,legacy['order'])
 for ident in s.get('operations',{}).get('orders',{}):s.setdefault('jobs',{}).setdefault(ident,{})
 for ident,j in s.get('jobs',{}).items():
  from improvements import dossier_state,payment_id
  j['state']=dossier_state(s,ident)
  for projected_invoice in [j.get('sales_invoice',{})]+j.get('invoice_archive',[]):
   for n,pay in enumerate(projected_invoice.get('payments',[])):pay.setdefault('id',payment_id(projected_invoice,n))
  j['dossier_flow']=dossier_flow(s,ident)
  j['registered_material_complete']=registered_material_complete(s,ident);j['labor_rate_reference']=labor_rate_reference(s,ident);j['invoice_proposal']=invoice_proposal(s,ident);j['invoice_control']=invoice_control(s,ident)
  j['status']=job_status(s,ident,j.get('status','open'))
  if j.get('waiting_part'):j['customer_followup']=customer_followup_view(j,s.get('operations',{}).get('orders',{}).get(ident,{}).get('customer','klant'))
 if s.get('registered'):
  j=s.setdefault('jobs',{}).setdefault('W105',{})
  j.setdefault('sales_invoice',existing_w105(s));inv=j['sales_invoice']
  j.update(completed=True,status=inv['status'],hours=s['hours'])
  status=('Concept CF105 gecontroleerd · nog te factureren' if s['reviewed'] else 'Concept CF105 · controle nodig') if inv['status']=='concept' else 'Factuur '+inv['id']+' · '+inv['status']
  from improvements import dossier_state
  j['state']=dossier_state(s,'W105');j['dossier_flow']=dossier_flow(s,'W105')
  status=j['state']['label'];todo['Administratie']=status
  todo['Eigenaar']=status
 delivery=('De cilinder is ontvangen.' if s['delivery_status']=='ontvangen' else f"Levering van uw cilinder is {'bevestigd' if s['delivery_status']=='bevestigd' else 'nog niet bevestigd'} voor {dutch_date(s['delivery_at'])}.")
 contact=('Uw akkoord is vastgelegd; u hoeft niet opnieuw te bevestigen.' if s['contact']=='fictief akkoord' else 'Wilt u deze afspraak bevestigen?')
 progress=('De montagegegevens zijn geregistreerd.' if s['registered'] else '')
 message=f"Beste Atelier Noord (fictief), {delivery} Uw afspraak met Bram staat op {dutch_date(s['appointment'])}. {contact} {progress} CONCEPT — nooit verzonden."
 labels={'confirm':'Levering bevestigd','receive':'Levering ontvangen','reschedule':'Afspraak verzet','contact':'Klantcontact bijgewerkt','register':'Uren opgeslagen','review':'Concept gecontroleerd','note':'Eigen demo-werknotitie opgeslagen','reopen':'Dossier aanpassen expliciet geopend'}
 for h in s['history']:
  h['label']=h.get('label',labels.get(h['action'],'Dossier bijgewerkt'))
  h.setdefault('at',None)

 if s['reviewed']:
  action='invoice_final' if inv['status']=='concept' and inv.get('due') else 'invoice_due' if inv['status']=='concept' else 'invoice_send' if inv['status']=='definitief' else 'payment' if inv['paid_cents']<inv['total_cents'] else None
  next_step=dict(role='Administratie',action=action,text=status)
 elif s['registered']:next_step=dict(role='Administratie',action='review',text='Controleer conceptfactuur CF105.')
 elif s['delivery_status']=='onbevestigd':next_step=dict(role='Lina',action='confirm',text='Bevestig de verwachte levering.')
 elif s['appointment']<s['delivery_at']:next_step=dict(role='Eigenaar',action='reschedule',text='Verzet de afspraak tot na de levering.')
 elif s['contact']!='fictief akkoord':next_step=dict(role='Eigenaar',action='contact',text='Leg het fictieve klantakkoord vast.')
 elif s['delivery_status']!='ontvangen':next_step=dict(role='Lina',action='receive',text='Markeer het onderdeel fictief ontvangen.')
 else:next_step=dict(role='Bram',action='register',text='Registreer uren en gebruikt materiaal.')
 if s.get('registered'):
  f=s['jobs']['W105']['dossier_flow'];next_step=dict(role='Administratie',action=f['target'],text=f['title'])
 if not s['registered'] and s['delivery_status']=='ontvangen' and s['appointment']>=s['delivery_at'] and s['contact']!='fictief akkoord':status='wacht op klantakkoord'
 s.update(next_step=next_step,status=status,todo=todo,responsible=dict(levering='Lina',planning='Eigenaar',montage='Bram',conceptfactuur='Administratie'),message=message,invoice=dict(id='CF105',status='concept gecontroleerd' if s['reviewed'] else 'concept',hours=s['hours'],hour_rate_cents=6000,materials=s['materials'],material_rate_cents=15000,net_cents=net,vat_cents=vat,total_cents=net+vat,source='W105 — dezelfde monteursregistratie; geen dubbel invoeren'),metrics=dict(saved_actions=len(s['history']),entered_fields=2 if s['registered'] else 0,duplicate_fields_avoided=2 if s['registered'] else 0,illustration_seconds=None,assumption='Geen gemeten tijdwinst. Bij W105 gaan twee opgeslagen bronvelden (uren en materiaalaantal) automatisch naar het concept. De getelde acties zijn geslaagde demo-opslagacties.'))
 if s.get('registered'):
  inv=s['jobs']['W105']['sales_invoice'];lines=inv['lines']
  s['invoice'].update(id=inv['id'],status=status,hours=lines[0]['quantity'],hour_rate_cents=lines[0]['unit_cents'],materials=lines[1]['quantity'] if len(lines)>1 else 0,material_rate_cents=lines[1]['unit_cents'] if len(lines)>1 else 0,net_cents=inv['net_cents'],vat_cents=inv['vat_cents'],total_cents=inv['total_cents'])
 return s
def persist(s):
 FILE.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
 fd,name=tempfile.mkstemp(dir=FILE.parent,prefix='workflow-')
 try:
  with os.fdopen(fd,'w') as f:json.dump(s,f);f.flush();os.fsync(f.fileno())
  os.replace(name,FILE)
 finally:
  if os.path.exists(name):os.unlink(name)

def apply(v):
 if not isinstance(v,dict) or v.get('role') not in ROLES:raise ValueError('Kies een demorol')
 with LOCK:
  s=load()
  request_id=v.get('request_id');fingerprint=hashlib.sha256(json.dumps({k:val for k,val in v.items() if k not in {'revision','request_id'}},sort_keys=True).encode()).hexdigest()
  if request_id is not None:
   if not isinstance(request_id,str) or not 1<=len(request_id)<=80 or not all(c.isalnum() or c in '-_' for c in request_id):raise ValueError('Ongeldig aanvraagnummer')
   receipt=s.get('request_receipts',{}).get(request_id)
   if receipt:
    if receipt['fingerprint']!=fingerprint:raise ValueError('Aanvraagnummer al voor een andere wijziging gebruikt')
    return view(s)
  if type(v.get('revision')) is not int or v['revision']!=s['revision']:raise ValueError('Dossier gewijzigd: ververs en probeer opnieuw')
  a=v.get('action');role=v['role'];job=v.get('job','W105')
  from business import mutate
  from improvements import ACTIONS,change
  if s.get('jobs',{}).get(job,{}).get('cancelled') and a not in {'note'}:raise ValueError('Opdracht geannuleerd; historie blijft beschikbaar')
  if a in {'trial_decisions','trial_accept'}:
   from delivery import mutate as trial_mutate
   trial_mutate(s,v);a='business_done'
  if a=='migration_commit':
   from pilot import commit_import
   commit_import(s,v);a='business_done'
  if a in ACTIONS:
   change(s,v);a='business_done'
  if a in {'quote_start','admin_close','billing_save','billing_apply','tariff_save','invoice_hours_apply','invoice_hours_reason','visit_hours','part_purchase','part_ordered','part_confirm','part_receive','part_cancel','customer_followup','followup_plan','waiting_part_clear','timeblock_link','waiting_part','timeblock','timeblock_remove','worktime','invoice_followup','invoice_due','invoice_draft','invoice_revise','invoice_final','invoice_send','payment','quote_save','quote_accept','intake','plan','stock_receive','reserve','stock_use','purchase','purchase_receive','key_authorize','key_revoke','key_issue','installation','communication','warranty','warranty_decide','sale','quote_new'}:
   mutate(s,v)
   a='business_done'
  if job not in {'W101','W102','W103','W104','W105','W106'} and job not in s.get('operations',{}).get('orders',{}):raise ValueError('Onbekende klus')
  allowed={'confirm':'Lina','receive':'Lina','reschedule':'Eigenaar','contact':'Eigenaar','register':'Bram','review':'Administratie','reset':'Eigenaar','note':('Bram' if job=='W104' else 'Lina'),'reopen':role,'repair':'Bram','handoff':'Bram','followup':'Lina','finish':'Bram','business_done':role}
  if allowed.get(a)!=role:raise ValueError('Deze actie hoort bij een andere demorol')
  if (job=='W104' and a not in {'reopen','note','repair','handoff','finish','business_done'}) or (job=='W106' and a not in ({'reopen','note','followup','business_done','finish','repair','handoff'} if s.get('jobs',{}).get('W106',{}).get('accepted') else {'note','followup','business_done'})) or (job=='W105' and a in {'repair','handoff','followup'}):raise ValueError('Actie hoort niet bij deze klus')
  if a=='note' and job=='W105':raise ValueError('Gebruik de W105 workflow')
  if job=='W105' and s['reviewed'] and not s.get('editing',False) and a not in {'reopen','business_done'}:raise ValueError('Afgerond dossier is alleen-lezen; kies Dossier aanpassen')
  if a=='reset':
   jobs=s.get('jobs',{});s=initial(s['revision']+1);s['jobs']=jobs
  else:
   if a in {'repair','handoff','followup','finish'}:
    j=s.setdefault('jobs',{}).setdefault(job,{})
    if a=='followup':
     note=v.get('call_note');date=v.get('followup_date')
     if not isinstance(note,str) or not note.strip() or len(note)>1000:raise ValueError('Vul een belnotitie in (max. 1000 tekens)')
     if not isinstance(date,str) or len(date)!=10:raise ValueError('Vul de volgende opvolgdatum in')
     datetime.strptime(date,'%Y-%m-%d')
     j.update(call_note=note.strip(),followup_date=date,status='opvolging gepland',responsible='Lina')
    elif a in {'repair','finish'}:
     op=s.get('operations',{}).get('orders',{}).get(job,{})
     if a=='finish' and op.get('agreement_required') and (not (j.get('direct_agreement') or j.get('accepted')) or not j.get('planning')):raise ValueError('Leg eerst klantakkoord en planning vast')
     waiting=j.get('waiting_part',{})
     if a=='finish' and waiting and (waiting.get('status') not in {'ontvangen','geannuleerd'} or (waiting.get('status')=='ontvangen' and not j.get('followup_planning'))):raise ValueError('Handel eerst de onderdeelontvangst en vervolgplanning af; bewaar diagnose als concept')
     if j.get('completed'):raise ValueError('Reeds gereedgemeld; administratie verwerkt deze registratie')
     findings=v.get('findings');hours=v.get('hours');materials=v.get('materials')
     if j.get('diagnosis_visit'):
      visits=v.get('visit_hours',j.get('visit_hours'))
      if not isinstance(visits,dict):raise ValueError('Registreer uren per diagnose- en vervolgbezoek; onbekend mag leeg blijven in concept')
      keys=['diagnosis']+(['followup'] if j.get('followup_planning') else [])
      for key in keys:
       h=visits.get(key)
       if h is not None and (type(h) not in (int,float) or not math.isfinite(h) or not 0<=h<=24):raise ValueError('Ongeldige bezoekuren')
      known=all(visits.get(key) is not None for key in keys)
      if a=='finish' and not known:raise ValueError('Vul alle bezoekuren in; onbekend is geen nul')
      hours=sum(visits[key] for key in keys) if known else None
      j['visit_hours']={key:visits.get(key) for key in keys}
     if not isinstance(findings,str) or len(findings)>1000 or (a=='finish' and not findings.strip()):raise ValueError('Vul bevindingen in (max. 1000 tekens)')
     if not (a=='repair' and hours is None) and (type(hours) not in (int,float) or not math.isfinite(hours) or not 0<=hours<=24 or (a=='finish' and hours==0)):raise ValueError('Vul geldige uren in (meer dan 0, maximaal 24)')
     from business import registered_material_complete
     if a=='finish' and any(r['order']==job and r['status']=='gereserveerd' for r in s.get('operations',{}).get('reservations',{}).values()):raise ValueError('Open materiaalreserveringen eerst verbruiken of afhandelen')
     if not isinstance(materials,str) or len(materials)>1000 or (a=='finish' and not materials.strip() and not registered_material_complete(s,job)):raise ValueError('Licht niet-geregistreerd of onduidelijk materiaal toe (of vermeld geen materiaal); open reserveringen eerst verwerken')
     j.update(findings=findings.strip(),hours=hours,materials=materials.strip(),status='in uitvoering — concept opgeslagen',responsible='Bram')
     if a=='finish':j.update(status='Nog te factureren',responsible='Administratie',completed=True,completed_date=__import__('data').DAY)
    else:
     from business import registered_material_complete
     if not j.get('findings') or not j.get('hours') or (not j.get('materials') and not registered_material_complete(s,job)):raise ValueError('Bewaar eerst bevindingen, uren en materiaal')
     j.update(status='Nog te factureren',responsible='Administratie',completed=True,completed_date=__import__('data').DAY)
   elif a=='note':
    note=v.get('note','')
    if not isinstance(note,str) or not note.strip() or len(note)>1000:raise ValueError('Vul een eigen demo-werknotitie in (max. 1000 tekens)')
    s.setdefault('jobs',{}).setdefault(job,{})['note']=note.strip()
   elif a=='reopen':
    if job=='W105':s['editing']=True
    else:
     j=s.setdefault('jobs',{}).setdefault(job,{})
     if j.get('sales_invoice',{}).get('status','concept')!='concept':raise ValueError('Definitieve factuur: afzonderlijke correctie vereist')
     j.pop('sales_invoice',None);j.update(completed=False,status='in uitvoering — concept opgeslagen',responsible='Bram')
   elif a=='confirm':
    if s['delivery_status']!='onbevestigd':raise ValueError('Levering al bevestigd')
    s['delivery_status']='bevestigd'
   elif a=='receive':
    if s['delivery_status']!='bevestigd':raise ValueError('Bevestig eerst levering')
    s['delivery_status']='ontvangen'
   elif a=='reschedule':
    at=v.get('appointment','');dt=datetime.fromisoformat(at)
    if dt.tzinfo is not None or len(at)!=16 or at<s['delivery_at'] or not at.startswith('2026-10-27T') or s['delivery_status']=='onbevestigd' or s['registered']:raise ValueError('Kies 27 oktober na levering; bevestig levering eerst')
    s['appointment']=at;s['contact']='opnieuw bevestigen nodig'
   elif a=='contact':
    if v.get('contact') not in ['niet benaderd','concept bekeken','fictief akkoord']:raise ValueError('Onbekende contactstatus')
    if s['appointment']<s['delivery_at']:raise ValueError('Herplan eerst de afspraak')
    s['contact']=v['contact']
   elif a=='register':
    inv=s.get('jobs',{}).get('W105',{}).get('sales_invoice')
    if inv and inv['status']!='concept':raise ValueError('Factuur definitief; registratie corrigeren vereist afzonderlijke correctie')
    s.get('jobs',{}).get('W105',{}).pop('sales_invoice',None)
    h=v.get('hours');m=v.get('materials')
    if type(h) not in (int,float) or not 0<h<=8 or type(m) is not int or not 0<=m<=20:raise ValueError('Vul uren groter dan 0 en maximaal 8 in, en 0–20 cilinders')
    if s['delivery_status']!='ontvangen' or s['appointment']<s['delivery_at'] or s['contact']!='fictief akkoord':raise ValueError('Eerst ontvangst, herplanning en fictief klantakkoord')
    reason=v.get('material_reason','')
    if not isinstance(reason,str) or len(reason)>300:raise ValueError('Materiaalreden maximaal 300 tekens')
    s.update(hours=h,materials=m,material_reason=reason.strip(),registered=True,reviewed=False)
    s.setdefault('jobs',{}).setdefault('W105',{})['completed_date']=__import__('data').DAY
   elif a=='review':
    if not s['registered']:raise ValueError('Eerst monteursregistratie')
    s['reviewed']=True;s['editing']=False
   s['history'].append(dict(details={k:val for k,val in v.items() if k not in {'revision','role','action','job','actor','payload'}},actor=v.get('actor'),business_date=__import__('data').DAY,role=role,action=v['action'],job=v.get('order',job),at=datetime.now(timezone.utc).isoformat(),sequence=len(s['history'])+1));s['revision']+=1
  if request_id:s.setdefault('request_receipts',{})[request_id]=dict(fingerprint=fingerprint,revision=s['revision'])
  persist(s)
  return view(s)
