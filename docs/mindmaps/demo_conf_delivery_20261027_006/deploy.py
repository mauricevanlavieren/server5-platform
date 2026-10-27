import json,subprocess,hashlib
from pathlib import Path
p=Path(__file__).parent
for n in ['delivery-test-results.txt','accounting-adapter-results.txt','regression-results.txt','demo-regression-results.txt']:assert '\nOK\n' in (p/n).read_text(),n
assert json.loads((p/'delivery-browser-results.json').read_text())['result']=='PASS'
names=['accounting.py','delivery.py','secure_app.py','security.py','data.py','workflow.py','recovery.py','README.md','aankoopbeslissingen.md','proefvoorstel.md','backup-herstel.md','backup-config.example.json','static/proefvoorstel.html','static/delivery.js','static/index.html','static/pilot.html','static/pilot.js','static/praktijkproef.html']
files={n:(p/n).read_text() for n in names};expected={n:hashlib.sha256((p/'original'/n).read_bytes()).hexdigest() if (p/'original'/n).exists() else None for n in names}
script='FILES='+repr(files)+'\nEXPECTED='+repr(expected)+'\nREFERENCE='+repr((p/'live-reference.json').read_bytes())+'\n'+r'''
from pathlib import Path
import os,subprocess,json,hashlib,shutil,time,urllib.request,py_compile,sqlite3
assert subprocess.check_output(['hostname'],text=True).strip()=='server4'
root=Path('/home/mau/server4-mobile-demo');state=Path.home()/'.local/state/server4-mobile-demo';before=(state/'workflow.json').read_bytes();assert before==REFERENCE,'Live business data changed; preserve and revalidate'
for n,h in EXPECTED.items():assert (hashlib.sha256((root/n).read_bytes()).hexdigest() if (root/n).exists() else None)==h,n+' changed concurrently'
with sqlite3.connect('file:'+str(state/'accounts.sqlite3')+'?mode=ro',uri=True) as d:users=d.execute('select count(*) from users').fetchone()[0]
backup=root/'backups/demo_conf_delivery_20261027_006';backup.mkdir(mode=0o700,exist_ok=False)
for n in FILES:
 if (root/n).exists():
  target=backup/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/n,target)
(backup/'workflow-reference.json').write_bytes(before)
os.environ['XDG_RUNTIME_DIR']='/run/user/'+str(os.getuid());os.environ['DBUS_SESSION_BUS_ADDRESS']='unix:path='+os.environ['XDG_RUNTIME_DIR']+'/bus'
try:
 subprocess.run(['systemctl','--user','stop','server4-mobile-demo.service'],check=True)
 assert (state/'workflow.json').read_bytes()==before
 for n,v in FILES.items():
  target=root/n;target.parent.mkdir(parents=True,exist_ok=True);tmp=target.with_suffix(target.suffix+'.delivery-tmp');tmp.write_text(v);tmp.replace(target)
  if n.endswith('.py'):py_compile.compile(str(target),doraise=True)
 subprocess.run(['systemctl','--user','start','server4-mobile-demo.service'],check=True)
 for _ in range(25):
  try:health=json.load(urllib.request.urlopen('http://127.0.0.1:8764/health',timeout=2));break
  except OSError:time.sleep(.2)
 assert health['status']=='ok' and health['demo_access']=='passwordless-fictional'
 import sys;sys.path.insert(0,str(root));import workflow;from pilot import reconcile;from data import accounting_csv;from delivery import read
 control=reconcile();assert control['balanced'];assert len(control['source_issues'])==19
 trial=read(workflow.load(),state/'offhost-backup-status.json');assert trial['external_backup']['result']=='PENDING_OWNER_DECISION';assert trial['external_import']=='niet gevalideerd';assert not trial['decisions']
 assert (state/'workflow.json').read_bytes()==before
 with sqlite3.connect('file:'+str(state/'accounts.sqlite3')+'?mode=ro',uri=True) as d:assert d.execute('select count(*) from users').fetchone()[0]==users
 snapshot=json.loads(subprocess.check_output([str(root/'.venv/bin/python'),str(root/'recovery.py')],text=True))
 print(json.dumps(dict(result='PASS',hostname='server4',health=health,source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in FILES},workflow_sha256=hashlib.sha256(before).hexdigest(),workflow_byte_identical=True,user_count=users,users_unchanged=True,backup=str(backup),local_snapshot=snapshot,control_totals=control['expected'],source_issues=len(control['source_issues']),export_sha256=hashlib.sha256(accounting_csv()).hexdigest(),external_backup='nog niet ingericht en getest',external_import=trial['external_import'],owner_decisions='open; no prices or support invented'),indent=2))
except BaseException:
 subprocess.run(['systemctl','--user','stop','server4-mobile-demo.service'])
 for n in FILES:
  if (backup/n).exists():shutil.copy2(backup/n,root/n)
  elif EXPECTED[n] is None:(root/n).unlink(missing_ok=True)
 subprocess.run(['systemctl','--user','start','server4-mobile-demo.service'],check=True)
 raise
'''
r=subprocess.run(['ssh','-F','/dev/null','-i','/home/mau/.ssh/id_ed25519_server5_servers12','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','IdentitiesOnly=yes','-o','IdentityAgent=none','-o','HostKeyAlgorithms=ssh-ed25519','mau@192.168.1.163','python3 -'],input=script,text=True,capture_output=True)
(p/'deployment-results.json').write_text(r.stdout if r.returncode==0 else json.dumps(dict(result='FAILED',stdout=r.stdout,stderr=r.stderr),indent=2));print('Deployment:',r.returncode);print(r.stderr);raise SystemExit(r.returncode)
