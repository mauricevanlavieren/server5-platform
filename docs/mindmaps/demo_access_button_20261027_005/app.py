#!/usr/bin/env python3
"""Loopback-only demo, stdlib runtime; private SSH route supplies authentication."""
import json,os,secrets,tempfile,threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit
from data import dashboard,TILES
from answers import answer
from workflow import view as workflow_view,apply as workflow_apply
BASE=Path(__file__).resolve().parent
STATE=Path.home()/'.local/state/server4-mobile-demo'
LOCK=threading.Lock()
DEFAULT=dict(visible=TILES,order=TILES)

def config():
 try:
  value=json.loads((STATE/'tiles.json').read_text())
  old=value.get('order',[])
  if set(old)!=set(TILES):return dict(order=TILES,visible=TILES)
  return value
 except FileNotFoundError:return DEFAULT.copy()

def save(value):
 if not isinstance(value,dict) or set(value)!={'visible','order'}:raise ValueError('Ongeldige configuratie')
 if any(not isinstance(value[k],list) for k in ('visible','order')):raise ValueError('Lijst vereist')
 if any(not isinstance(x,str) for k in value for x in value[k]):raise ValueError('Tegelnaam vereist')
 if set(value['order'])!=set(TILES) or len(value['order'])!=len(TILES):raise ValueError('Volgorde moet alle unieke tegels bevatten')
 if not set(value['visible'])<=set(TILES) or len(set(value['visible']))!=len(value['visible']):raise ValueError('Onbekende of dubbele tegel')
 STATE.mkdir(mode=0o700,parents=True,exist_ok=True)
 with LOCK:
  fd,name=tempfile.mkstemp(dir=STATE,prefix='tiles-')
  try:
   with os.fdopen(fd,'w') as f:json.dump(value,f);f.flush();os.fsync(f.fileno())
   os.replace(name,STATE/'tiles.json')
  finally:
   if os.path.exists(name):os.unlink(name)
 return value

class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass # no questions, audio, cookies or querystrings in logs
 def reply(self,status,body,kind='application/json; charset=utf-8'):
  if not isinstance(body,bytes):body=json.dumps(body,ensure_ascii=False).encode()
  self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(body)))
  self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer')
  self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
  self.send_header('Permissions-Policy','microphone=(self), camera=(), geolocation=()');self.end_headers();self.wfile.write(body)
 def valid_host(self):
  return self.headers.get('Host','').split(':')[0].lower() in ('127.0.0.1','localhost')
 def do_GET(self):
  if not self.valid_host():return self.reply(403,dict(error='Alleen lokale toegang via private tunnel'))
  path=urlsplit(self.path).path
  if path=='/health':return self.reply(200,dict(status='ok',data='fictional',ai='local-rules',external_ai_required=False))
  if path=='/praktijkproef':return self.reply(200,(BASE/'static/praktijkproef.html').read_bytes(),'text/html; charset=utf-8')
  if path=='/api/dashboard':return self.reply(200,dict(**dashboard(),config=config()))
  if path=='/api/accounting-export':
   from data import accounting_csv
   return self.reply(200,accounting_csv(),'text/csv; charset=utf-8')
  if path=='/api/workflow':return self.reply(200,workflow_view())
  if path=='/api/config':return self.reply(200,config())
  assets={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),'/style.css':('style.css','text/css; charset=utf-8')}
  if path in assets:
   name,kind=assets[path];return self.reply(200,(BASE/'static'/name).read_bytes(),kind)
  self.reply(404,dict(error='Niet gevonden'))
 def do_POST(self):
  if not self.valid_host():return self.reply(403,dict(error='Ongeldige host'))
  # Browser POST must come from the exact local origin; no cross-origin configuration changes.
  origin=self.headers.get('Origin','')
  if origin and origin not in ('http://'+self.headers['Host'],'https://'+self.headers['Host']):return self.reply(403,dict(error='Ongeldige oorsprong'))
  if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.reply(415,dict(error='JSON vereist'))
  try:
   length=int(self.headers.get('Content-Length','0'))
   if length<1 or length>4096:return self.reply(413,dict(error='Invoer te groot of leeg'))
   value=json.loads(self.rfile.read(length));path=urlsplit(self.path).path
   if path=='/api/ask':
    q=value.get('question') if isinstance(value,dict) else None
    if not isinstance(q,str) or not q.strip() or len(q)>500:raise ValueError('Vraag moet 1–500 tekens bevatten')
    return self.reply(200,answer(q.strip()))
   if path=='/api/workflow':return self.reply(200,workflow_apply(value))
   if path=='/api/config':return self.reply(200,save(value))
   self.reply(404,dict(error='Niet gevonden'))
  except OSError:return self.reply(503,dict(error='Opslag niet bevestigd. Je invoer blijft staan; controleer de actuele gegevens of probeer dezelfde aanvraag opnieuw.'))
  except (ValueError,TypeError,UnicodeError) as e:self.reply(400,dict(error=str(e) or 'Ongeldige invoer'))
 def setup(self):super().setup();self.connection.settimeout(5)

if __name__=='__main__':
 ThreadingHTTPServer(('127.0.0.1',8764),Handler).serve_forever()
