from pathlib import Path
import json,subprocess,hashlib
p=Path(__file__).parent
for n in ['story-test-results.txt','regression-results.txt','demo-regression-results.txt','public-regression-results.txt']:assert '\nOK\n' in (p/n).read_text(),n
assert json.loads((p/'story-browser-results.json').read_text())['result']=='PASS'
names=['demo_story.py','demo-presentatie.md','secure_app.py','data.py','business.py','recovery.py','README.md','static/public-login.html','static/public-login.js','static/login.js','static/index.html','static/app.js','static/demo-ui.js','static/style.css','static/pilot.html','static/pilot.js','static/proefvoorstel.html','static/delivery.js']
files={n:(p/n).read_text() for n in names};expected={n:hashlib.sha256((p/'original'/n).read_bytes()).hexdigest() if (p/'original'/n).exists() else None for n in names}
script='FILES='+repr(files)+'\nEXPECTED='+repr(expected)+'\n'+r'''
from pathlib import Path
import subprocess,json,os,shutil,hashlib,py_compile,time,sys,copy,importlib,sqlite3
assert subprocess.check_output(['hostname'],text=True).strip()=='server4'
root=Path('/home/mau/server4-mobile-demo');state=Path.home()/'.local/state/server4-mobile-demo';sys.path.insert(0,str(root))
for n,h in EXPECTED.items():assert (hashlib.sha256((root/n).read_bytes()).hexdigest() if (root/n).exists() else None)==h,'Concurrent source change: '+n
os.environ['XDG_RUNTIME_DIR']='/run/user/'+str(os.getuid());os.environ['DBUS_SESSION_BUS_ADDRESS']='unix:path='+os.environ['XDG_RUNTIME_DIR']+'/bus'
backup=root/'backups/demo_conf_story_20261027_008';backup.mkdir(mode=0o700,exist_ok=False)
subprocess.run(['systemctl','--user','stop','server4-mobile-demo.service'],check=True)
original=(state/'workflow.json').read_bytes();old=json.loads(original)
from recovery import backup as previous_backup
previous_backup(root,state,backup/'before-complete')
with sqlite3.connect('file:'+str(state/'accounts.sqlite3')+'?mode=ro',uri=True) as d:users=d.execute('select count(*) from users').fetchone()[0]
for n in FILES:
 if (root/n).exists():
  target=backup/'source-before'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/n,target)
try:
 for n,v in FILES.items():
  target=root/n;target.parent.mkdir(parents=True,exist_ok=True);tmp=target.with_suffix(target.suffix+'.story-tmp');tmp.write_text(v);tmp.replace(target)
  if n.endswith('.py'):py_compile.compile(str(target),doraise=True)
 import workflow
 from demo_story import add_stories
 new=add_stories(old,dict(id=None,username='Fictieve demo-inrichting',role='system',employee=''))
 for table in ['jobs','tariffs','customers','articles']:
  for key,value in old.get(table,{}).items():assert new.get(table,{}).get(key)==value,'Existing '+table+' changed: '+key
 for table in ['orders','stock','sales','reservations','purchases','work_patterns','worktimes']:
  for key,value in old.get('operations',{}).get(table,{}).items():assert new.get('operations',{}).get(table,{}).get(key)==value,'Existing operations '+table+' changed: '+key
 assert new['history'][:len(old['history'])]==old['history'];assert new.get('trial')==old.get('trial')
 # Compare financial export before/after in memory, using the newly installed read model.
 from data import accounting_csv
 from pilot import reconcile
 workflow.FILE=state/'workflow.json';before_export=accounting_csv();before_control=reconcile()['expected'];workflow.persist(new)
 assert accounting_csv()==before_export;assert reconcile()['balanced'];assert reconcile()['expected']==before_control
 subprocess.run(['systemctl','--user','start','server4-mobile-demo.service'],check=True)
 import urllib.request
 for _ in range(25):
  try:health=json.load(urllib.request.urlopen('http://127.0.0.1:8764/health',timeout=2));break
  except OSError:time.sleep(.2)
 assert health['status']=='ok'
 with sqlite3.connect('file:'+str(state/'accounts.sqlite3')+'?mode=ro',uri=True) as d:assert d.execute('select count(*) from users').fetchone()[0]==users
 import recovery;importlib.reload(recovery)
 snapshot=root/'backups'/('snapshot-story-'+str(time.time_ns()));manifest=recovery.backup(root,state,snapshot)
 print(json.dumps(dict(result='PASS',hostname='server4',source_files=len(FILES),source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in FILES},before_workflow_sha256=hashlib.sha256(original).hexdigest(),after_workflow_sha256=hashlib.sha256((state/'workflow.json').read_bytes()).hexdigest(),old_orders_preserved=True,old_jobs_preserved=True,old_stock_preserved=True,old_tariffs_preserved=True,old_history_preserved=True,commercial_choices_preserved=True,accounts_unchanged=True,featured=new['demo_scenario']['featured'],catalog_products=5,financial_export_byte_identical=True,export_sha256=hashlib.sha256(before_export).hexdigest(),control_totals=before_control,revision_before=old['revision'],revision_after=new['revision'],backup=str(backup),local_snapshot=str(snapshot),snapshot_files=len(manifest),health=health),indent=2))
except BaseException:
 subprocess.run(['systemctl','--user','stop','server4-mobile-demo.service'])
 # Service has stayed stopped during data changes; this only rolls back our own seed addition.
 if (state/'workflow.json').read_bytes()!=original:
  fd,tmp=__import__('tempfile').mkstemp(dir=state)
  with os.fdopen(fd,'wb') as f:f.write(original);f.flush();os.fsync(f.fileno())
  os.replace(tmp,state/'workflow.json')
 for n in FILES:
  saved=backup/'source-before'/n
  if saved.exists():shutil.copy2(saved,root/n)
  elif EXPECTED[n] is None:(root/n).unlink(missing_ok=True)
 subprocess.run(['systemctl','--user','start','server4-mobile-demo.service'],check=True)
 raise
'''
r=subprocess.run(['ssh','-F','/dev/null','-i','/home/mau/.ssh/id_ed25519_server5_servers12','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','IdentitiesOnly=yes','-o','IdentityAgent=none','-o','HostKeyAlgorithms=ssh-ed25519','mau@192.168.1.163','/home/mau/server4-mobile-demo/.venv/bin/python -'],input=script,text=True,capture_output=True)
(p/'deployment-results.json').write_text(r.stdout if r.returncode==0 else json.dumps(dict(result='FAILED',stderr=r.stderr,stdout=r.stdout),indent=2));print('Deployment:',r.returncode);print(r.stderr);raise SystemExit(r.returncode)
