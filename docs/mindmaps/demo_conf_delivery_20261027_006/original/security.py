"""Local accounts, Werkzeug scrypt and revocable server-side sessions."""
import os,secrets,sqlite3,time,hashlib,re
from pathlib import Path
from werkzeug.security import generate_password_hash,check_password_hash
ROLES={'owner','mechanic','administration'}
class Accounts:
 def __init__(self,state):
  self.state=state;state.mkdir(mode=0o700,parents=True,exist_ok=True)
  self.path=state/'accounts.sqlite3'
  with self.db() as d:
   d.executescript('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,username TEXT UNIQUE NOT NULL,password TEXT NOT NULL,role TEXT NOT NULL,employee TEXT NOT NULL,active INTEGER NOT NULL DEFAULT 1); CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY,user_id INTEGER,expires REAL); CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,at REAL,user_id INTEGER,action TEXT,subject TEXT); CREATE TABLE IF NOT EXISTS attempts(name TEXT PRIMARY KEY,failures INTEGER,until REAL);''')
  os.chmod(self.path,0o600)
  self.secret=state/'session-secret'
  if not self.secret.exists():
   fd=os.open(self.secret,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
   with os.fdopen(fd,'w') as f:f.write(secrets.token_hex(32))
  with self.db() as d:empty=d.execute('select count(*) from users').fetchone()[0]==0
  token=state/'owner-activation'
  if empty and not token.exists():
   fd=os.open(token,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
   with os.fdopen(fd,'w') as f:f.write(secrets.token_urlsafe(32))
 def db(self):
  d=sqlite3.connect(self.path,timeout=10);d.row_factory=sqlite3.Row;return d
 def create(self,v,actor=None,bootstrap=False):
  name=v.get('username','');password=v.get('password','');role=v.get('role');employee=v.get('employee','')
  if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9_.-]{3,60}',name):raise ValueError('Gebruikersnaam: 3–60 letters, cijfers, punt, streepje')
  if not isinstance(password,str) or not 12<=len(password)<=128:raise ValueError('Wachtwoord: 12–128 tekens')
  if role not in ROLES or employee not in {'','Bram','Noor','Lina'} or (role=='mechanic' and not employee):raise ValueError('Kies geldige rol en medewerker voor monteur')
  digest=generate_password_hash(password)
  with self.db() as d:
   d.execute('BEGIN IMMEDIATE')
   if bootstrap and d.execute('select count(*) from users').fetchone()[0]:raise ValueError('Eigenaar is al ingericht')
   try:cur=d.execute('insert into users(username,password,role,employee) values(?,?,?,?)',(name,digest,role,employee))
   except sqlite3.IntegrityError:raise ValueError('Gebruikersnaam bestaat al')
   d.execute('insert into audit(at,user_id,action,subject) values(?,?,?,?)',(time.time(),actor or cur.lastrowid,'user_created',name))
  return cur.lastrowid
 def login(self,name,password):
  if not isinstance(name,str) or not isinstance(password,str) or len(name)>60 or len(password)>128:return None
  with self.db() as d:
   a=d.execute('select * from attempts where name=?',(name,)).fetchone()
   if a and a['until']>time.time():return None
   u=d.execute('select * from users where username=? and active=1',(name,)).fetchone()
   if not u or not check_password_hash(u['password'],password):
    failures=(a['failures'] if a else 0)+1
    d.execute('insert or replace into attempts values(?,?,?)',(name,failures,time.time()+300 if failures>=5 else 0));return None
   d.execute('delete from attempts where name=?',(name,));sid=secrets.token_urlsafe(32)
   d.execute('insert into sessions values(?,?,?)',(hashlib.sha256(sid.encode()).hexdigest(),u['id'],time.time()+8*3600))
   d.execute('insert into audit(at,user_id,action,subject) values(?,?,?,?)',(time.time(),u['id'],'login',name))
   return sid,dict(id=u['id'],username=u['username'],role=u['role'],employee=u['employee'])
 def demo_login(self):
  sid=secrets.token_urlsafe(32)
  with self.db() as d:
   d.execute('delete from sessions where expires<?',(time.time(),))
   d.execute('insert into sessions values(?,?,?)',(hashlib.sha256(sid.encode()).hexdigest(),None,time.time()+8*3600))
   d.execute('insert into audit(at,user_id,action,subject) values(?,?,?,?)',(time.time(),None,'demo_entered','Gedeelde fictieve demo'))
  return sid
 def current(self,sid):
  if not isinstance(sid,str):return None
  with self.db() as d:
   u=d.execute('select s.user_id,u.id,u.username,u.role,u.employee from sessions s left join users u on s.user_id=u.id where s.id=? and s.expires>? and (s.user_id is null or u.active=1)',(hashlib.sha256(sid.encode()).hexdigest(),time.time())).fetchone()
   if not u:return None
   if u['user_id'] is None:return dict(id=None,username='Demobezoeker',role='demo',employee='')
   return {k:u[k] for k in ('id','username','role','employee')}
 def logout(self,sid):
  with self.db() as d:d.execute('delete from sessions where id=?',(hashlib.sha256(sid.encode()).hexdigest(),))
 def revoke(self,uid,actor):
  with self.db() as d:
   u=d.execute('select * from users where id=?',(uid,)).fetchone()
   if not u or uid==actor:raise ValueError('Kies een andere bestaande gebruiker')
   if u['role']=='owner' and d.execute("select count(*) from users where role='owner' and active=1").fetchone()[0]<=1:raise ValueError('Laatste eigenaar behouden')
   d.execute('update users set active=0 where id=?',(uid,));d.execute('delete from sessions where user_id=?',(uid,))
   d.execute('insert into audit(at,user_id,action,subject) values(?,?,?,?)',(time.time(),actor,'user_disabled',str(uid)))

MECHANIC={'register','note','repair','finish','handoff','visit_hours','reserve','stock_use','reservation_release','material_return'}
ADMIN={'invoice_draft','invoice_due','invoice_final','invoice_send','payment','invoice_followup','admin_close','accounting_mark','review'}
class Forbidden(Exception):pass

def assigned(s,u):
 from data import ORDERS
 orders={o['id']:o for o in ORDERS};orders.update(s.get('operations',{}).get('orders',{}))
 return {k for k,o in orders.items() if (s.get('jobs',{}).get(k,{}).get('followup_planning') or s.get('jobs',{}).get(k,{}).get('planning') or o).get('employee')==u['employee']}

def authorize(s,u,v):
 a=v.get('action');job=v.get('job',v.get('order','W105'))
 if u['role'] in {'owner','demo'}:return dict(v,actor=dict(u))
 if u['role']=='mechanic':
  if a not in MECHANIC or job not in assigned(s,u):raise Forbidden('Alleen uitvoering van eigen toegewezen opdrachten toegestaan')
  if v.get('order',job)!=job:raise Forbidden('Opdrachtverwijzingen verschillen')
  if a=='reserve' and any(k in v for k in ('unit_cents','price_source','rate_cents','price_cents')):raise Forbidden('Prijswijzigingen horen bij eigenaar')
  r=v.get('reservation')
  if r and s.get('operations',{}).get('reservations',{}).get(r,{}).get('order')!=job:raise Forbidden('Reservering hoort bij een ander dossier')
  if a=='material_return' and s.get('jobs',{}).get(job,{}).get('sales_invoice',{}).get('status','concept')!='concept':raise Forbidden('Definitieve financiële correctie vereist eigenaar')
  # The legacy workflow distinguishes display actors; authority comes only from u.
  legacy='Bram'
  if a=='note':legacy='Bram' if job=='W104' else 'Lina'
 elif u['role']=='administration':
  if a not in ADMIN:raise Forbidden('Deze wijziging vereist eigenaar of toegewezen monteur')
  # Administration cannot change tariffs through the concept-generation endpoint.
  if a=='invoice_draft':
   from business import labor_rate_reference
   ref=labor_rate_reference(s,job)
   fixed=s.get('jobs',{}).get(job,{}).get('billing',{}).get('mode') in {'fixed','extra'}
   if not fixed and (not ref or v.get('rate_cents')!=ref.get('unit_cents') or not ref.get('unit_cents')):raise Forbidden('Eigenaar moet eerst een herleidbaar tarief vastleggen en gebruiken')
   for rid,price in v.get('material_prices',{}).items():
    material=s.get('operations',{}).get('reservations',{}).get(rid,{})
    if price.get('unit_cents')!=material.get('unit_cents') or price.get('source')!=material.get('price_source'):raise Forbidden('Materiaalprijs wijzigen vereist eigenaar')
   if any(v.get(k) is not None for k in ('material_unit_cents','material_quantity','material_source')):raise Forbidden('Niet-geregistreerd materiaal vereist controle door eigenaar')
  legacy='Administratie'
 else:raise Forbidden('Onbekende gebruikersrol')
 return dict(v,role=legacy,actor=dict(u))

def mechanic_view(s,u):
 from data import ORDERS
 orders={o['id']:o for o in ORDERS};orders.update(s.get('operations',{}).get('orders',{}))
 result=[]
 for k in sorted(assigned(s,u)):
  o=orders[k];j=s.get('jobs',{}).get(k,{})
  fields={key:j[key] for key in ('findings','hours','materials','completed','planning','followup_planning','visit_hours','diagnosis_visit','note','status') if key in j}
  result.append(dict(id=k,customer=o['customer'],scope=o.get('scope',o.get('job','')),**fields))
 reservations=[{k:r.get(k) for k in ('id','order','key','quantity','status')} for r in s.get('operations',{}).get('reservations',{}).values() if r['order'] in assigned(s,u)]
 return dict(revision=s['revision'],orders=result,reservations=reservations)
