"""Reproducible fictitious demo stories; reset archives before atomic replacement."""
import copy,hashlib,json,re,secrets,os,tempfile
from datetime import datetime,timezone
from pathlib import Path
VERSION=1
CATALOG=[('Cilinderslot SKG** 30/30 mm — demo',12,3500),('Loper universeel — demo',8,1250),('Insteekslot 55 mm — demo',6,4900),('Deurdranger standaard — demo',5,8500),('Veiligheidscilinder SKG*** 30/35 — demo',3,15000)]

def add_stories(source,actor=None):
 """Append only; existing orders, facts, prices and histories are preserved."""
 if source.get('demo_scenario',{}).get('version')==VERSION:return copy.deepcopy(source)
 from business import operate,mutate
 from improvements import change
 from data import DAY
 s=copy.deepcopy(source);ops=s.setdefault('operations',{})
 for key in ('orders','stock','purchases','reservations','authorizations','sales'):ops.setdefault(key,{})
 ops.setdefault('events',[])
 def op(action,**values):operate(s,dict(role='Eigenaar',action=action,job=values.pop('job','W104'),actor=actor,**values))
 def mutate_job(action,job,**values):mutate(s,dict(role='Eigenaar',action=action,job=job,actor=actor,**values))
 articles=s.setdefault('articles',{})
 for n,(name,quantity,price) in enumerate(CATALOG,1):
  key=name+' @ winkel'
  if key not in ops['stock']:op('stock_receive',part=name,location='winkel',quantity=quantity,source='Fictieve standaardvoorraad Sleutelhuis; geen echte ontvangst')
  articles.setdefault('DEMO-SH-'+str(n),dict(id='DEMO-SH-'+str(n),name=name,location='winkel',unit_cents=price,vat_percent=21,quantity=quantity,source='Fictieve catalogus; geen productaanbod'))
 featured=[]
 for customer,scope,priority,kind,employee in [
  ('Familie Janssens (fictief)','Spoed: slot vervangen na sleutelverlies','spoed','intake','Bram'),
  ('VvE Parkzicht (fictief)','Inplannen: onderhoud hang- en sluitwerk','normaal','quote_new','Lina'),
  ('Bakkerij De Hoek (fictief)','Vervolgbezoek: veiligheidscilinder vervangen','normaal','intake','Noor')]:
  fields=dict(customer=customer,contact='Fictieve contactpersoon',scope=scope,priority=priority)
  if kind=='intake':fields.update(address='Fictieve Voorbeeldstraat '+str(len(featured)+1),phone='0000000000',access='Afspraak via fictieve contactpersoon; geen codes of sleutels')
  op(kind,**fields);ident=list(ops['orders'])[-1];ops['orders'][ident]['employee']=employee;j=s.setdefault('jobs',{}).setdefault(ident,{})
  if kind=='quote_new':
   mutate_job('quote_save',ident,scope=scope,net_cents=15000,source='Fictieve vaste onderhoudsprijs')
   mutate_job('quote_accept',ident,confirmed=True,agreement='Fictief akkoord VvE-beheerder; standaarddemo')
   mutate_job('billing_save',ident,mode='fixed',approval_who='VvE-beheerder (fictief)',approval_date=DAY,approval_reference='DEMO-VVE',reason='Fictieve vaste prijs voor onderhoud; geen echte overeenkomst')
  else:change(s,dict(role='Eigenaar',action='direct_agreement',job=ident,who='Klant (fictief)',date=DAY,reference='DEMO-AKKOORD-'+ident,actor=actor))
  if customer not in s.get('tariffs',{}):mutate_job('tariff_save',ident,customer=customer,rate_cents=6000,source='Fictief demonstratietarief; geen aanbod')
  if len(featured)==2:
   op('waiting_part',job=ident,order=ident,part='Veiligheidscilinder SKG*** 40/50 maatwerk — demo',supplier='Fictieve leverancier Sluitwerk',responsible='Lina',followup_date=DAY,expected_delivery='2026-10-27')
   j.update(findings='Fictieve diagnose: cilindermaat gecontroleerd; levering en vervolg afstemmen.',hours=0.5,materials='Nog geen materiaal verbruikt')
  featured.append(ident)
 # Existing rosters are never overwritten by seed preparation.
 patterns=ops.setdefault('work_patterns',{})
 if not source.get('history'):
  for employee in ('Bram','Lina','Noor'):patterns.setdefault(employee,dict(days=[0,1,2,3,4],start='08:00',end='17:00',source='Fictief standaardrooster; geen echte medewerkerplanning'))
 now=datetime.now(timezone.utc).isoformat()
 runs=ops.setdefault('demo_runs',[]);run_id='D'+str(len(runs)+1)
 runs.append(dict(id=run_id,created_at=now,monteur=featured[0],onderdeel=featured[2],article=CATALOG[0][0],quantity=CATALOG[0][1],source='Gevulde fictieve standaarddemo; bestaande rondes behouden'))
 s['demo_scenario']=dict(version=VERSION,epoch=secrets.token_hex(8),featured=featured,article=CATALOG[0][0],prepared_at=now,fictional=True)
 s.setdefault('history',[]).append(dict(action='demo_story_prepared',role='Eigenaar',actor=actor,job=featured[0],at=now,business_date=DAY,sequence=len(s['history'])+1,details=dict(orders=featured,source='Nieuwe fictieve voorbeelden; bestaande gegevens bewaard')))
 s['revision']=source['revision']+1
 return s

def standard(revision,actor=None):
 from workflow import initial
 return add_stories(initial(revision-1),actor)

def reset(state,values,actor):
 from workflow import LOCK,load,persist,view
 from data import DAY
 if actor.get('role')!='owner':raise PermissionError('Reset demo is alleen beschikbaar voor de eigenaar via de private route')
 rid=values.get('request_id');revision=values.get('revision')
 if not isinstance(rid,str) or not re.fullmatch('[A-Za-z0-9_-]{1,80}',rid):raise ValueError('Herlaad de pagina en probeer de reset opnieuw')
 with LOCK:
  old=load();key='demo-reset:'+rid;receipt=old.get('request_receipts',{}).get(key)
  if receipt:return dict(message='Demo staat op de gevulde standaardstatus. Vorige gegevens zijn bewaard.',archive_id=receipt['archive_id'],workflow=view(old),replayed=True)
  if type(revision) is not int or revision!=old['revision']:raise ValueError('Demo gewijzigd in een andere sessie. Herlaad voordat je opnieuw reset.')
  replacement=standard(old['revision']+1,actor)
  # Commercial decisions are settings, never erased by a fictional data reset.
  trial=old.get('trial',{})
  if trial:replacement['trial']={k:copy.deepcopy(v) for k,v in trial.items() if k!='acceptance'}
  root=state/'demo-reset-archives';root.mkdir(parents=True,mode=0o700,exist_ok=True)
  archive_id='reset-'+str(old['revision'])+'-'+secrets.token_hex(8)
  record=dict(archive_id=archive_id,at=datetime.now(timezone.utc).isoformat(),actor=actor,previous_revision=old['revision'],history_count=len(old.get('history',[])),order_count=len(old.get('operations',{}).get('orders',{})),workflow_sha256=hashlib.sha256(json.dumps(old,sort_keys=True).encode()).hexdigest(),state=old)
  # Archive must be durable before the current state can be replaced.
  fd,name=tempfile.mkstemp(dir=root)
  try:
   with os.fdopen(fd,'w') as f:json.dump(record,f);f.flush();os.fsync(f.fileno())
   os.replace(name,root/(archive_id+'.json'));directory=os.open(root,os.O_RDONLY)
   try:os.fsync(directory)
   finally:os.close(directory)
  finally:
   if os.path.exists(name):os.unlink(name)
  replacement['request_receipts']=copy.deepcopy(old.get('request_receipts',{}));replacement['request_receipts'][key]=dict(archive_id=archive_id)
  replacement['demo_reset_history']=copy.deepcopy(old.get('demo_reset_history',[]))+[{k:v for k,v in record.items() if k!='state'}]
  replacement['history'].append(dict(action='demo_reset',role='Eigenaar',actor=actor,job='W104',at=record['at'],business_date=DAY,sequence=len(replacement['history'])+1,details=dict(archive_id=archive_id,previous_revision=old['revision'])))
  persist(replacement)
  return dict(message='Demo hersteld: drie startverhalen, voorraad en voorbeeldfacturen. Vorige gegevens zijn bewaard.',archive_id=archive_id,workflow=view(replacement),replayed=False)
