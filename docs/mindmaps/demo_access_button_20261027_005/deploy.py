import json,subprocess,hashlib
from pathlib import Path
p=Path(__file__).parent
names=['secure_app.py','security.py','README.md','static/login.html','static/login.js','static/app.js','static/pilot.js','static/praktijkproef.html']
assert '\nOK\n' in (p/'test-results.txt').read_text();assert '\nOK\n' in (p/'regression-results.txt').read_text();assert json.loads((p/'test-browser-results.json').read_text())['result']=='PASS'
files={n:(p/n).read_text() for n in names};expected={n:hashlib.sha256((p/'original'/n).read_bytes()).hexdigest() for n in names}
script='FILES='+repr(files)+'\nEXPECTED='+repr(expected)+'\n'+r'''
from pathlib import Path
import os,subprocess,json,hashlib,shutil,time,urllib.request,py_compile,sqlite3
assert subprocess.check_output(['hostname'],text=True).strip()=='server4'
root=Path('/home/mau/server4-mobile-demo');state=Path.home()/'.local/state/server4-mobile-demo';before=(state/'workflow.json').read_bytes()
for n,h in EXPECTED.items():assert hashlib.sha256((root/n).read_bytes()).hexdigest()==h,n+' changed concurrently'
with sqlite3.connect('file:'+str(state/'accounts.sqlite3')+'?mode=ro',uri=True) as d:users_before=d.execute('select count(*) from users').fetchone()[0]
backup=root/'backups/demo_access_button_20261027_005';backup.mkdir(mode=0o700,exist_ok=False)
for n in FILES:
 target=backup/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/n,target)
os.environ['XDG_RUNTIME_DIR']='/run/user/'+str(os.getuid());os.environ['DBUS_SESSION_BUS_ADDRESS']='unix:path='+os.environ['XDG_RUNTIME_DIR']+'/bus'
try:
 subprocess.run(['systemctl','--user','stop','server4-mobile-demo.service'],check=True)
 for n,v in FILES.items():
  target=root/n;tmp=target.with_suffix(target.suffix+'.demo-access-tmp');tmp.write_text(v);tmp.replace(target)
  if n.endswith('.py'):py_compile.compile(str(target),doraise=True)
 subprocess.run(['systemctl','--user','start','server4-mobile-demo.service'],check=True)
 for _ in range(25):
  try:
   health=json.load(urllib.request.urlopen('http://127.0.0.1:8764/health',timeout=2));break
  except OSError:time.sleep(.2)
 assert health['demo_access']=='passwordless-fictional'
 assert (state/'workflow.json').read_bytes()==before
 with sqlite3.connect('file:'+str(state/'accounts.sqlite3')+'?mode=ro',uri=True) as d:assert d.execute('select count(*) from users').fetchone()[0]==users_before
 snapshot=json.loads(subprocess.check_output([str(root/'.venv/bin/python'),str(root/'recovery.py')],text=True))
 print(json.dumps(dict(result='PASS',hostname='server4',health=health,source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in FILES},workflow_sha256=hashlib.sha256(before).hexdigest(),workflow_byte_identical=True,user_count=users_before,users_unchanged=True,backup=str(backup),snapshot=snapshot),indent=2))
except BaseException:
 subprocess.run(['systemctl','--user','stop','server4-mobile-demo.service'])
 for n in FILES:shutil.copy2(backup/n,root/n)
 subprocess.run(['systemctl','--user','start','server4-mobile-demo.service'],check=True)
 raise
'''
r=subprocess.run(['ssh','-F','/dev/null','-i','/home/mau/.ssh/id_ed25519_server5_servers12','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','IdentitiesOnly=yes','-o','IdentityAgent=none','-o','HostKeyAlgorithms=ssh-ed25519','mau@192.168.1.163','python3 -'],input=script,text=True,capture_output=True)
(p/'deployment-results.json').write_text(r.stdout if r.returncode==0 else json.dumps(dict(result='FAILED',stdout=r.stdout,stderr=r.stderr),indent=2));print('Deployment:',r.returncode);print(r.stderr);raise SystemExit(r.returncode)
