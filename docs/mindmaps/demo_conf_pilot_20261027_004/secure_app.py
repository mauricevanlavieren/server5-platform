"""Authenticated loopback application. One process, existing workflow retained."""
import json,os,secrets,sqlite3,hashlib,time
from pathlib import Path
from flask import Flask,request,session,g,jsonify,send_from_directory,redirect,Response
import workflow,app as legacy
from security import Accounts,Forbidden,authorize,mechanic_view
from data import dashboard,accounting_csv
from answers import answer
BASE=Path(__file__).resolve().parent

def create_app(state=None):
 state=Path(state or os.environ.get('DEMO_STATE',Path.home()/'.local/state/server4-mobile-demo'))
 workflow.FILE=state/'workflow.json';legacy.STATE=state
 accounts=Accounts(state)
 app=Flask(__name__,static_folder=None)
 app.config.update(SECRET_KEY=accounts.secret.read_text(),SESSION_COOKIE_NAME='server4_session',SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Strict',SESSION_COOKIE_SECURE=os.environ.get('DEMO_HTTPS')=='1',MAX_CONTENT_LENGTH=262144,PERMANENT_SESSION_LIFETIME=8*3600)
 app.accounts=accounts
 @app.before_request
 def guard():
  if request.host.split(':')[0].lower() not in {'127.0.0.1','localhost'}:return jsonify(error='Alleen lokale private tunnel toegestaan'),403
  g.user=accounts.current(session.get('sid'))
  if request.method=='POST':
   if request.headers.get('Origin') and request.headers['Origin']!=request.host_url.rstrip('/'):return jsonify(error='Ongeldige oorsprong'),403
   if not request.is_json:return jsonify(error='JSON vereist'),415
   if not isinstance(request.get_json(silent=True),dict):return jsonify(error='JSON-object vereist'),400
   if request.path not in {'/api/login','/api/activate'} and (not session.get('csrf') or not secrets.compare_digest(request.headers.get('X-CSRF-Token',''),session['csrf'])):return jsonify(error='Sessiecontrole mislukt; herlaad en meld aan'),403
  public={'/health','/login','/login.js','/style.css','/api/login','/api/activate'}
  if request.path not in public and not g.user:
   if request.path.startswith('/api/'):return jsonify(error='Aanmelden vereist'),401
   return redirect('/login')
  if g.user and g.user['role']=='mechanic' and request.path not in public|{'/','/pilot','/pilot.js','/api/session','/api/logout','/api/mechanic','/api/workflow','/praktijkproef'}:raise Forbidden('Deze gegevens zijn niet beschikbaar voor monteurs')
  if g.user and g.user['role']=='mechanic' and request.path=='/api/workflow' and request.method=='GET':raise Forbidden('Gebruik uitsluitend eigen toegewezen dossiers')
 @app.after_request
 def headers(r):
  r.headers.update({'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",'Permissions-Policy':'microphone=(self), camera=(), geolocation=()'})
  return r
 @app.errorhandler(Forbidden)
 def denied(e):return jsonify(error=str(e)),403
 @app.errorhandler(ValueError)
 @app.errorhandler(TypeError)
 def bad(e):return jsonify(error=str(e) or 'Ongeldige invoer'),400
 @app.errorhandler(OSError)
 def storage(e):return jsonify(error='Opslag niet bevestigd. Invoer behouden; controleer en herhaal dezelfde aanvraag.'),503
 @app.get('/health')
 def health():return jsonify(status='ok',data='fictional',authentication='accounts',external_ai_required=False)
 @app.get('/login')
 def login_page():return send_from_directory(BASE/'static','login.html')
 @app.post('/api/activate')
 def activate():
  v=request.get_json();token=state/'owner-activation'
  if not token.exists() or not isinstance(v.get('activation'),str) or not secrets.compare_digest(v['activation'],token.read_text().strip()):raise Forbidden('Ongeldige of verbruikte lokale activering')
  accounts.create(dict(v,role='owner',employee=''),bootstrap=True)
  token.unlink(missing_ok=True)
  return jsonify(message='Eigenaar ingericht. Meld nu aan.')
 @app.post('/api/login')
 def login():
  v=request.get_json();result=accounts.login(v.get('username'),v.get('password'))
  if not result:return jsonify(error='Aanmelden mislukt of tijdelijk geblokkeerd'),401
  old=session.get('sid')
  if old:accounts.logout(old)
  session.clear();session['sid']=result[0];session['csrf']=secrets.token_urlsafe(32);session.permanent=True
  return jsonify(user=result[1],csrf=session['csrf'])
 @app.get('/api/session')
 def current():return jsonify(user=g.user,csrf=session['csrf'])
 @app.post('/api/logout')
 def logout():accounts.logout(session['sid']);session.clear();return jsonify(message='Afgemeld')
 @app.get('/')
 def home():return send_from_directory(BASE/'static','pilot.html' if g.user['role']=='mechanic' else 'index.html')
 @app.get('/pilot')
 def pilot_page():return send_from_directory(BASE/'static','pilot.html')
 @app.get('/praktijkproef')
 def commercial():return send_from_directory(BASE/'static','praktijkproef.html')
 @app.get('/<name>')
 def asset(name):
  if name not in {'app.js','pilot.js','login.js','style.css'}:return jsonify(error='Niet gevonden'),404
  return send_from_directory(BASE/'static',name)
 @app.get('/api/dashboard')
 def dash():
  with workflow.LOCK:return jsonify(dict(**dashboard(),config=legacy.config()))
 @app.get('/api/workflow')
 def read_workflow():return jsonify(workflow.view())
 @app.post('/api/workflow')
 def write_workflow():
  with workflow.LOCK:
   value=request.get_json()
   if not isinstance(value,dict):raise ValueError('JSON-object vereist')
   if value.get('action') in {'migration_commit'} and g.user['role']!='owner':raise Forbidden('Migratie vereist eigenaar')
   result=workflow.apply(authorize(workflow.load(),g.user,value))
   return jsonify(mechanic_view(workflow.load(),g.user) if g.user['role']=='mechanic' else result)
 @app.get('/api/config')
 def config():return jsonify(legacy.config())
 @app.post('/api/config')
 def set_config():
  owner();return jsonify(legacy.save(request.get_json()))
 @app.post('/api/ask')
 def ask():
  v=request.get_json();q=v.get('question')
  if not isinstance(q,str) or not 1<=len(q.strip())<=500:raise ValueError('Vraag: 1–500 tekens')
  return jsonify(answer(q.strip()))
 @app.get('/api/mechanic')
 def mywork():
  if g.user['role']!='mechanic':raise Forbidden('Alleen monteurs')
  with workflow.LOCK:return jsonify(mechanic_view(workflow.load(),g.user))
 def owner():
  if g.user['role']!='owner':raise Forbidden('Alleen eigenaar')
 @app.get('/api/users')
 def users():
  owner()
  with accounts.db() as d:return jsonify(users=[dict(r) for r in d.execute('select id,username,role,employee,active from users')])
 @app.post('/api/users')
 def create_user():owner();return jsonify(id=accounts.create(request.get_json(),actor=g.user['id']))
 @app.post('/api/users/disable')
 def disable_user():owner();accounts.revoke(request.get_json().get('id'),g.user['id']);return jsonify(message='Gebruiker en sessies beëindigd')
 @app.get('/api/audit')
 def audit():
  owner()
  with accounts.db() as d:rows=[dict(r) for r in d.execute('select a.*,u.username from audit a left join users u on u.id=a.user_id order by a.id desc limit 200')]
  with workflow.LOCK:history=workflow.load().get('history',[])[-200:]
  return jsonify(accounts=rows,workflow=history)
 @app.get('/api/accounting-export')
 def export():
  with workflow.LOCK:return Response(accounting_csv(),mimetype='text/csv')
 @app.get('/api/reconciliation')
 def reconciliation():
  from pilot import reconcile
  with workflow.LOCK:return jsonify(reconcile())
 @app.post('/api/migration/preview')
 def preview():
  owner();from pilot import preview_import
  with workflow.LOCK:return jsonify(preview_import(workflow.load(),request.get_json()))
 @app.get('/api/catalog')
 def catalog():
  owner();s=workflow.load();return jsonify(customers=s.get('customers',{}),articles=s.get('articles',{}))
 @app.get('/api/migration/history')
 def imports():
  owner();return jsonify(imports=workflow.load().get('migration_history',[]))
 return app

if __name__=='__main__':
 from waitress import serve
 serve(create_app(),host='127.0.0.1',port=int(os.environ.get('DEMO_PORT','8764')),threads=4,clear_untrusted_proxy_headers=True)
