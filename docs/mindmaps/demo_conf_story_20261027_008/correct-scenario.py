from pathlib import Path
import json,hashlib,subprocess
p=Path(__file__).parent;d=json.loads((p/'deployment-results.json').read_text());content=(p/'demo_story.py').read_text();script='EXPECTED='+repr(d['source_sha256']['demo_story.py'])+'\nCONTENT='+repr(content)+'\n'+r'''
from pathlib import Path
import json,os,subprocess,hashlib,time,copy
root=Path('/home/mau/server4-mobile-demo');state=Path.home()/'.local/state/server4-mobile-demo';target=root/'demo_story.py'
assert hashlib.sha256(target.read_bytes()).hexdigest()==EXPECTED
os.environ['XDG_RUNTIME_DIR']='/run/user/'+str(os.getuid());os.environ['DBUS_SESSION_BUS_ADDRESS']='unix:path='+os.environ['XDG_RUNTIME_DIR']+'/bus'
subprocess.run(['systemctl','--user','stop','server4-mobile-demo.service'],check=True)
import sys;sys.path.insert(0,str(root));import workflow
old=workflow.load();saved=root/'backups/demo_conf_story_20261027_008/scenario-review';saved.mkdir(mode=0o700,exist_ok=False);(saved/'demo_story.py').write_bytes(target.read_bytes());(saved/'workflow-reference.json').write_bytes((state/'workflow.json').read_bytes())
try:
 tmp=target.with_suffix('.py.review-tmp');tmp.write_text(CONTENT);tmp.replace(target)
 s=copy.deepcopy(old);ident=s['demo_scenario']['featured'][2];j=s['jobs'][ident];part=j.get('waiting_part',{});changed=False
 if part.get('part')=='Veiligheidscilinder SKG*** 30/35 — demo' and part.get('status')=='behoefte geregistreerd' and not any(p.get('order')==ident for p in s['operations'].get('purchases',{}).values()) and not any(r.get('order')==ident for r in s['operations'].get('reservations',{}).values()):
  before=part['part'];part['part']='Veiligheidscilinder SKG*** 40/50 maatwerk — demo'
  from datetime import datetime,timezone
  s['history'].append(dict(role='Eigenaar',action='demo_story_scenario_correction',actor=dict(id=None,username='Fictieve demo-inrichting',role='system'),job=ident,at=datetime.now(timezone.utc).isoformat(),business_date=__import__('data').DAY,sequence=len(s['history'])+1,details=dict(before=before,after=part['part'],reason='Maatwerkvariant ontbreekt; standaardvariant is wel op voorraad.')));s['revision']+=1;workflow.persist(s);changed=True
 from pilot import reconcile
 from data import accounting_csv
 assert reconcile()['balanced']
 subprocess.run(['systemctl','--user','start','server4-mobile-demo.service'],check=True)
 import recovery
 snapshot=root/'backups'/('snapshot-story-final-'+str(time.time_ns()));manifest=recovery.backup(root,state,snapshot)
 print(json.dumps(dict(result='PASS',source_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),scenario_corrected=changed,job=ident,required_part=part.get('part'),required_part_stock=s['operations']['stock'].get(part.get('part','')+' @ winkel',0),history_appended=changed,old_history_retained=s['history'][:len(old['history'])]==old['history'],revision_after=s['revision'],after_workflow_sha256=hashlib.sha256((state/'workflow.json').read_bytes()).hexdigest(),local_snapshot=str(snapshot),snapshot_files=len(manifest),export_sha256=hashlib.sha256(accounting_csv()).hexdigest()),indent=2))
finally:
 subprocess.run(['systemctl','--user','start','server4-mobile-demo.service'],check=True)
'''
r=subprocess.run(['ssh','-F','/dev/null','-i','/home/mau/.ssh/id_ed25519_server5_servers12','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','IdentitiesOnly=yes','-o','IdentityAgent=none','-o','HostKeyAlgorithms=ssh-ed25519','mau@192.168.1.163','/home/mau/server4-mobile-demo/.venv/bin/python -'],input=script,text=True,capture_output=True)
if r.returncode:raise RuntimeError(r.stderr)
v=json.loads(r.stdout);assert v['export_sha256']==d['export_sha256'];(p/'scenario-review-results.json').write_text(json.dumps(v,indent=2));d['source_sha256']['demo_story.py']=v['source_sha256'];d['local_snapshot']=v['local_snapshot'];d['snapshot_files']=v['snapshot_files'];d['revision_after']=v['revision_after'];d['after_workflow_sha256']=v['after_workflow_sha256'];(p/'deployment-results.json').write_text(json.dumps(d,indent=2));print(r.stdout)
