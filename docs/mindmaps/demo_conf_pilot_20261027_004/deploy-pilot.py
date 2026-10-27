import json,subprocess,hashlib
from pathlib import Path
p=Path(__file__).parent
names=['secure_app.py','security.py','pilot.py','requirements.txt','migratieformaat.md','aankoopbeslissingen.md','business.py','workflow.py','data.py','improvements.py','recovery.py','README.md','static/app.js','static/style.css','static/index.html','static/praktijkproef.html','static/login.html','static/login.js','static/pilot.html','static/pilot.js']
files={n:(p/n).read_text() for n in names}
original={n:hashlib.sha256((p/'original'/n).read_bytes()).hexdigest() if (p/'original'/n).exists() else None for n in names}
remote='ORIGINAL='+repr(original)+'\nFILES='+repr(files)+'\nREFERENCE='+repr((p/'live-reference.json').read_bytes())+'\n'+r'''
import os,sys,json,shutil,hashlib,subprocess,time,urllib.request,urllib.error,py_compile
from pathlib import Path
assert subprocess.check_output(['hostname'],text=True).strip()=='server4'
root=Path('/home/mau/server4-mobile-demo');state=Path.home()/'.local/state/server4-mobile-demo';before=(state/'workflow.json').read_bytes();assert before==REFERENCE,'Live data changed; stop deployment and revalidate new state'
for name,digest in ORIGINAL.items():assert (hashlib.sha256((root/name).read_bytes()).hexdigest() if (root/name).exists() else None)==digest,'Concurrent source change: '+name
os.environ['XDG_RUNTIME_DIR']='/run/user/'+str(os.getuid());os.environ['DBUS_SESSION_BUS_ADDRESS']='unix:path='+os.environ['XDG_RUNTIME_DIR']+'/bus'
backup=root/'backups/demo_conf_pilot_20261027_004';backup.mkdir(mode=0o700,exist_ok=False)
dropin=Path.home()/'.config/systemd/user/server4-mobile-demo.service.d/10-pilot.conf';assert not dropin.exists(),'Unexpected existing drop-in; preserve it'
(backup/'service-before.txt').write_text(subprocess.check_output(['systemctl','--user','cat','server4-mobile-demo.service'],text=True))
subprocess.run(['systemctl','--user','stop','server4-mobile-demo.service'],check=True)
try:
 assert (state/'workflow.json').read_bytes()==before,'Live mutation completed during stop; revalidate'
 for name in FILES:
  target=root/name
  if target.exists():
   saved=backup/name;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,saved)
 (backup/'workflow-reference.json').write_bytes(before)
 if (state/'tiles.json').exists():shutil.copy2(state/'tiles.json',backup/'tiles-reference.json')
 for name,content in FILES.items():
  target=root/name;target.parent.mkdir(parents=True,exist_ok=True);tmp=target.with_suffix(target.suffix+'.pilot-tmp');tmp.write_text(content);tmp.replace(target)
  if name.endswith('.py'):py_compile.compile(str(target),doraise=True)
 dropin.parent.mkdir(exist_ok=True);dropin.write_text('[Service]\nExecStart=\nExecStart=/home/mau/server4-mobile-demo/.venv/bin/python /home/mau/server4-mobile-demo/secure_app.py\n')
 subprocess.run(['systemctl','--user','daemon-reload'],check=True);subprocess.run(['systemctl','--user','start','server4-mobile-demo.service'],check=True)
 for attempt in range(30):
  try:
   with urllib.request.urlopen('http://127.0.0.1:8764/health',timeout=2) as r:health=json.load(r)
   break
  except OSError:time.sleep(.2)
 assert health['authentication']=='accounts';checks={}
 for endpoint in ['/api/dashboard','/api/workflow','/api/accounting-export','/api/users','/api/audit']:
  try:urllib.request.urlopen('http://127.0.0.1:8764'+endpoint,timeout=3)
  except urllib.error.HTTPError as e:assert e.code==401;checks[endpoint]=e.code
  else:raise AssertionError('Unauthenticated access: '+endpoint)
 for endpoint,filename in [('/login','static/login.html'),('/login.js','static/login.js'),('/style.css','static/style.css')]:
  with urllib.request.urlopen('http://127.0.0.1:8764'+endpoint,timeout=3) as r:assert r.read()==(root/filename).read_bytes();checks[endpoint]=r.status
 sys.path.insert(0,str(root));import workflow;from pilot import reconcile
 controls=reconcile();assert controls['balanced'],controls
 assert (state/'workflow.json').read_bytes()==before
 assert (state/'owner-activation').exists() and (state/'owner-activation').stat().st_mode&0o777==0o600
 snapshot=json.loads(subprocess.check_output([str(root/'.venv/bin/python'),str(root/'recovery.py')],text=True))
 hashes={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in FILES}
 print(json.dumps(dict(result='PASS',hostname='server4',health=health,endpoints=checks,live_state_sha256=hashlib.sha256(before).hexdigest(),live_state_byte_identical=True,backup=str(backup),snapshot=snapshot,source_sha256=hashes,reconciliation=controls,service=subprocess.check_output(['systemctl','--user','is-active','server4-mobile-demo.service'],text=True).strip(),first_owner='pending local activation; no credentials printed'),ensure_ascii=False,indent=2))
except BaseException:
 subprocess.run(['systemctl','--user','stop','server4-mobile-demo.service'])
 for name in FILES:
  target=root/name;saved=backup/name
  if saved.exists():shutil.copy2(saved,target)
  elif ORIGINAL[name] is None:target.unlink(missing_ok=True)
 dropin.unlink(missing_ok=True);subprocess.run(['systemctl','--user','daemon-reload'],check=True);subprocess.run(['systemctl','--user','start','server4-mobile-demo.service'],check=True)
 raise
'''
r=subprocess.run(['ssh','-F','/dev/null','-i','/home/mau/.ssh/id_ed25519_server5_servers12','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','IdentitiesOnly=yes','-o','IdentityAgent=none','-o','HostKeyAlgorithms=ssh-ed25519','mau@192.168.1.163','python3 -'],input=remote,text=True,capture_output=True)
(p/'deployment-results.json').write_text(r.stdout if r.returncode==0 else json.dumps(dict(result='FAILED',stderr=r.stderr,stdout=r.stdout),indent=2));print('Deployment exit',r.returncode);print(r.stderr);raise SystemExit(r.returncode)
