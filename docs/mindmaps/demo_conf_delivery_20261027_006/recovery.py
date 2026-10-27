#!/usr/bin/env python3
"""Consistent business snapshot + SQLite online backup; isolated restore only by default."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,shutil,tempfile,sqlite3,subprocess
SOURCES=['backup-config.example.json','accounting.py','backup-herstel.md','delivery.py','static/proefvoorstel.html','static/delivery.js','proefvoorstel.md','migratieformaat.md','aankoopbeslissingen.md','secure_app.py','security.py','pilot.py','requirements.txt','sales.py','static/praktijkproef.html','static/login.html','static/login.js','static/pilot.html','static/pilot.js','app.py','business.py','workflow.py','data.py','improvements.py','answers.py','README.md','recovery.py','static/app.js','static/index.html','static/style.css']
STATE_FILES=['workflow.json','tiles.json','accounts.sqlite3','session-secret','offhost-backup-status.json']

def backup(root,state,destination):
 destination.mkdir(parents=True,mode=0o700,exist_ok=False);manifest={}
 from workflow import LOCK
 with LOCK:
  source_before={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in SOURCES if (root/name).is_file()}
  for name in SOURCES:
   source=root/name
   if source.exists():
    target=destination/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
  for name in STATE_FILES:
   source=state/name
   if source.exists():
    target=destination/'state'/name;target.parent.mkdir(parents=True,mode=0o700,exist_ok=True)
    if name=='accounts.sqlite3':
     with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(target) as dest:src.backup(dest)
    else:target.write_bytes(source.read_bytes())
    os.chmod(target,0o600)
  source_after={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in SOURCES if (root/name).is_file()}
  copied_source={name:hashlib.sha256((destination/'source'/name).read_bytes()).hexdigest() for name in source_before}
  if source_before!=source_after or source_before!=copied_source:raise ValueError('Bron gewijzigd tijdens backup; geen geldige snapshot gepubliceerd')
 for file in destination.rglob('*'):
  if file.is_file():manifest[str(file.relative_to(destination))]=hashlib.sha256(file.read_bytes()).hexdigest()
 (destination/'manifest.json').write_text(json.dumps(manifest,indent=2));return manifest

def restore(root,state,source):
 # A restore is allowed only with both app/state destinations isolated, or the live service stopped.
 live=Path.home()/'.local/state/server4-mobile-demo'
 if state.resolve()==live.resolve():
  r=subprocess.run(['systemctl','--user','is-active','server4-mobile-demo.service'],capture_output=True,text=True)
  if r.returncode not in {3,4} or r.stdout.strip() not in {'inactive','failed','unknown'}:raise ValueError('Stop eerst de bestaande demo-service; live herstel geweigerd')
 manifest=json.loads((source/'manifest.json').read_text())
 if not isinstance(manifest,dict) or not manifest:raise ValueError('Leeg of ongeldig manifest')
 allowed={'source/'+name for name in SOURCES}|{'state/'+name for name in STATE_FILES}
 for name,digest in manifest.items():
  if name not in allowed or (source/name).is_symlink() or hashlib.sha256((source/name).read_bytes()).hexdigest()!=digest:raise ValueError('Backupbestand ongeldig: '+name)
  target=(root if name.startswith('source/') else state)/name.split('/',1)[1]
  if target.is_symlink() or any(p.is_symlink() for p in target.parents if p!=Path('/')):raise ValueError('Symlink in hersteldoel geweigerd')
 saved=root/'backups'/('before-restore-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));backup(root,state,saved)
 for name in manifest:
  target=(root if name.startswith('source/') else state)/name.split('/',1)[1];target.parent.mkdir(parents=True,mode=0o700,exist_ok=True)
  fd,tmp=tempfile.mkstemp(dir=target.parent)
  with os.fdopen(fd,'wb') as f:f.write((source/name).read_bytes());f.flush();os.fsync(f.fileno())
  os.replace(tmp,target)
 # Restored credentials remain valid, pre-restore browser sessions do not.
 if (state/'accounts.sqlite3').exists():
  with sqlite3.connect(state/'accounts.sqlite3') as d:d.execute('delete from sessions');d.execute('delete from attempts')
 return str(saved)

def external_copy(snapshot,target):
 target=target.resolve()
 if not target.is_dir() or target.stat().st_dev==snapshot.stat().st_dev:raise ValueError('Kies een bestaande geautoriseerde externe mount; zelfde filesystem geweigerd')
 destination=target/snapshot.name
 shutil.copytree(snapshot,destination);os.chmod(destination,0o700)
 manifest=json.loads((snapshot/'manifest.json').read_text())
 for name,digest in manifest.items():
  if hashlib.sha256((destination/name).read_bytes()).hexdigest()!=digest:raise ValueError('Externe kopiecontrole mislukt')
 return destination

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--restore',type=Path);parser.add_argument('--service-stopped',action='store_true');parser.add_argument('--external-destination',type=Path);a=parser.parse_args()
 root=Path(__file__).resolve().parent;state=Path.home()/'.local/state/server4-mobile-demo'
 if a.restore:
  if not a.service_stopped:parser.error('Stop eerst server4-mobile-demo.service en geef --service-stopped op')
  print(restore(root,state,a.restore))
 else:
  target=root/'backups'/('snapshot-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));manifest=backup(root,state,target);result=dict(path=str(target),files=len(manifest),external_copy='niet uitgevoerd')
  if a.external_destination:result['external_copy']=str(external_copy(target,a.external_destination))
  print(json.dumps(result))
