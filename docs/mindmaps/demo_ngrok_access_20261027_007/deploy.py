from pathlib import Path
import json,hashlib,subprocess
p=Path(__file__).parent;host=json.loads((p/'endpoint-before.json').read_text())['url'].split('://')[1]
for name in ['public-test-results.txt','regression-results.txt','demo-regression-results.txt']:assert '\nOK\n' in (p/name).read_text()
names=['secure_app.py','recovery.py','static/public-login.html','static/public-login.js'];files={n:(p/n).read_text() for n in names};expected={n:hashlib.sha256((p/'original'/n).read_bytes()).hexdigest() if (p/'original'/n).exists() else None for n in names}
script='FILES='+repr(files)+'\nEXPECTED='+repr(expected)+'\nHOST='+repr(host)+'\n'+r'''
from pathlib import Path
import hashlib,subprocess,os,json,shutil,py_compile,time,urllib.request
assert subprocess.check_output(['hostname'],text=True).strip()=='server4'
root=Path('/home/mau/server4-mobile-demo');state=Path.home()/'.local/state/server4-mobile-demo';before=(state/'workflow.json').read_bytes()
for n,h in EXPECTED.items():assert (hashlib.sha256((root/n).read_bytes()).hexdigest() if (root/n).exists() else None)==h,n
backup=root/'backups/demo_ngrok_access_20261027_007';backup.mkdir(mode=0o700,exist_ok=False)
for n in FILES:
 if (root/n).exists():
  saved=backup/n;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/n,saved)
dropin=Path.home()/'.config/systemd/user/server4-mobile-demo.service.d/20-public-demo.conf';assert not dropin.exists()
os.environ['XDG_RUNTIME_DIR']='/run/user/'+str(os.getuid());os.environ['DBUS_SESSION_BUS_ADDRESS']='unix:path='+os.environ['XDG_RUNTIME_DIR']+'/bus'
try:
 subprocess.run(['systemctl','--user','stop','server4-mobile-demo.service'],check=True)
 for n,v in FILES.items():
  target=root/n;tmp=target.with_suffix(target.suffix+'.public-tmp');tmp.write_text(v);tmp.replace(target)
  if n.endswith('.py'):py_compile.compile(str(target),doraise=True)
 dropin.write_text('[Service]\nEnvironment=PUBLIC_DEMO_HOST='+HOST+'\n')
 subprocess.run(['systemctl','--user','daemon-reload'],check=True);subprocess.run(['systemctl','--user','start','server4-mobile-demo.service'],check=True)
 for _ in range(25):
  try:health=json.load(urllib.request.urlopen('http://127.0.0.1:8764/health',timeout=2));break
  except OSError:time.sleep(.2)
 req=urllib.request.Request('http://127.0.0.1:8764/login',headers={'Host':HOST});body=urllib.request.urlopen(req).read();assert b'Toegang demo' in body and b'owner-activation' not in body
 assert (state/'workflow.json').read_bytes()==before
 snapshot=json.loads(subprocess.check_output([str(root/'.venv/bin/python'),str(root/'recovery.py')],text=True))
 print(json.dumps(dict(result='PASS',host='server4',public_host=HOST,health=health,source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in FILES},workflow_sha256=hashlib.sha256(before).hexdigest(),workflow_byte_identical=True,backup=str(backup),local_snapshot=snapshot),indent=2))
except BaseException:
 subprocess.run(['systemctl','--user','stop','server4-mobile-demo.service'])
 for n in FILES:
  if (backup/n).exists():shutil.copy2(backup/n,root/n)
  elif EXPECTED[n] is None:(root/n).unlink(missing_ok=True)
 dropin.unlink(missing_ok=True);subprocess.run(['systemctl','--user','daemon-reload'],check=True);subprocess.run(['systemctl','--user','start','server4-mobile-demo.service'],check=True)
 raise
'''
r=subprocess.run(['ssh','-F','/dev/null','-i','/home/mau/.ssh/id_ed25519_server5_servers12','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','IdentitiesOnly=yes','-o','IdentityAgent=none','-o','HostKeyAlgorithms=ssh-ed25519','mau@192.168.1.163','python3 -'],input=script,text=True,capture_output=True)
(p/'deployment-results.json').write_text(r.stdout if r.returncode==0 else json.dumps(dict(result='FAILED',stderr=r.stderr,stdout=r.stdout),indent=2));print('Deployment',r.returncode);print(r.stderr);raise SystemExit(r.returncode)
