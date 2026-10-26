import json,subprocess
from pathlib import Path
p=Path(__file__).parent
names=['app.py','business.py','workflow.py','data.py','improvements.py','recovery.py','README.md','static/app.js','static/style.css','static/index.html']
files={n:(p/n).read_text() for n in names}
import hashlib
original={n:hashlib.sha256((p/'original'/n).read_bytes()).hexdigest() for n in names}
remote='ORIGINAL='+repr(original)+'\nFILES='+repr(files)+'\nREFERENCE='+repr((p/'live-reference.json').read_bytes())+'\n'+r'''
import os,sys,json,shutil,hashlib,subprocess,time,urllib.request,py_compile
from pathlib import Path
assert subprocess.check_output(['hostname'],text=True).strip()=='server4'
root=Path('/home/mau/server4-mobile-demo');state=Path.home()/'.local/state/server4-mobile-demo/workflow.json';before=state.read_bytes();assert before==REFERENCE,'Live state changed: preserve and retest'
for name,digest in ORIGINAL.items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,'Source changed concurrently: '+name
backup=root/'backups/demo_conf_operations_20261026_003';backup.mkdir(exist_ok=False)
for name in FILES:
 target=root/name
 if target.exists():
  saved=backup/name;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,saved)
(backup/'workflow-reference.json').write_bytes(before)
config=state.with_name('tiles.json')
if config.exists():shutil.copy2(config,backup/'tiles-reference.json')
os.environ['XDG_RUNTIME_DIR']='/run/user/'+str(os.getuid());os.environ['DBUS_SESSION_BUS_ADDRESS']='unix:path='+os.environ['XDG_RUNTIME_DIR']+'/bus'
try:
 for name,content in FILES.items():
  target=root/name;tmp=target.with_suffix(target.suffix+'.demo-conf-tmp');tmp.write_text(content);tmp.replace(target)
  if name.endswith('.py'):py_compile.compile(str(target),doraise=True)
 subprocess.run(['systemctl','--user','restart','server4-mobile-demo.service'],check=True)
 for attempt in range(30):
  try:
   with urllib.request.urlopen('http://127.0.0.1:8764/health',timeout=3) as r:health=json.load(r)
   break
  except OSError:time.sleep(.2)
 checks={}
 for endpoint in ['/api/dashboard','/api/workflow','/api/accounting-export','/','/app.js','/style.css']:
  with urllib.request.urlopen('http://127.0.0.1:8764'+endpoint,timeout=5) as r:
   raw=r.read();checks[endpoint]=dict(status=r.status,sha256=hashlib.sha256(raw).hexdigest())
   if endpoint=='/api/workflow':view=json.loads(raw)
   if endpoint=='/api/dashboard':dashboard=json.loads(raw)
   if endpoint in ['/','/app.js','/style.css']:assert raw.decode()==FILES[{'/':'static/index.html','/app.js':'static/app.js','/style.css':'static/style.css'}[endpoint]]
 assert state.read_bytes()==before
 original=json.loads(before)
 for ident in ['W106','W109']:
  for field,value in original['jobs'][ident]['sales_invoice'].items():
   current=view['jobs'][ident]['sales_invoice'][field]
   if field=='payments':
    assert len(current)==len(value)
    for new,old in zip(current,value):assert all(new[k]==val for k,val in old.items())
   else:assert current==value
 assert all(j==original.get('jobs',{}).get(k) for k,j in json.loads(state.read_text())['jobs'].items())
 snapshot=subprocess.check_output(['python3',str(root/'recovery.py')],text=True).strip()
 print(json.dumps(dict(result='PASS',hostname='server4',health=health,endpoints=checks,live_state_sha256=hashlib.sha256(before).hexdigest(),live_state_byte_identical=True,backup=str(backup),new_snapshot=json.loads(snapshot),regressions=['W106','W109'],revenue_cents=dashboard['revenue_cents'],open_cents=dashboard['open_cents']),ensure_ascii=False,indent=2))
except BaseException:
 for name in FILES:
  target=root/name;saved=backup/name
  if saved.exists():shutil.copy2(saved,target)
  elif target.exists():target.unlink()
 subprocess.run(['systemctl','--user','restart','server4-mobile-demo.service'],check=True)
 raise
'''
r=subprocess.run(['ssh','-F','/dev/null','-i','/home/mau/.ssh/id_ed25519_server5_servers12','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','mau@192.168.1.163','python3 -'],input=remote,text=True,capture_output=True)
(p/'deployment-results.json').write_text(r.stdout if r.returncode==0 else json.dumps(dict(result='FAILED',stderr=r.stderr,stdout=r.stdout),indent=2));print(r.stdout);print(r.stderr);raise SystemExit(r.returncode)
