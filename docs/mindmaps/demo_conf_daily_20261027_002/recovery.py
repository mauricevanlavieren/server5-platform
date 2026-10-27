#!/usr/bin/env python3
"""Manual demo backup/restore. Stop the demo service before restore."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,shutil,tempfile
SOURCES=['app.py','business.py','workflow.py','data.py','improvements.py','answers.py','README.md','recovery.py','static/app.js','static/index.html','static/style.css']
def backup(root,state,destination):
 destination.mkdir(parents=True,mode=0o700,exist_ok=False);manifest={}
 for name in SOURCES:
  source=root/name
  if source.exists():
   target=destination/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
 for name in ['workflow.json','tiles.json']:
  source=state/name
  if source.exists():
   target=destination/'state'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
 for file in destination.rglob('*'):
  if file.is_file():manifest[str(file.relative_to(destination))]=hashlib.sha256(file.read_bytes()).hexdigest()
 (destination/'manifest.json').write_text(json.dumps(manifest,indent=2));return manifest

def restore(root,state,source):
 manifest=json.loads((source/'manifest.json').read_text())
 allowed={'source/'+name for name in SOURCES}|{'state/workflow.json','state/tiles.json'}
 for name,digest in manifest.items():
  if name not in allowed or hashlib.sha256((source/name).read_bytes()).hexdigest()!=digest:raise ValueError('Backupbestand ongeldig: '+name)
 # All checks finish before any file is replaced. Preserve current files first.
 saved=root/'backups'/('before-restore-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));backup(root,state,saved)
 for name in manifest:
  target=(root if name.startswith('source/') else state)/name.split('/',1)[1];target.parent.mkdir(parents=True,exist_ok=True)
  fd,tmp=tempfile.mkstemp(dir=target.parent)
  with os.fdopen(fd,'wb') as f:f.write((source/name).read_bytes());f.flush();os.fsync(f.fileno())
  os.replace(tmp,target)
 return str(saved)
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--restore',type=Path);parser.add_argument('--service-stopped',action='store_true');a=parser.parse_args()
 root=Path(__file__).resolve().parent;state=Path.home()/'.local/state/server4-mobile-demo'
 if a.restore:
  if not a.service_stopped:parser.error('Stop eerst server4-mobile-demo.service en geef --service-stopped op')
  print(restore(root,state,a.restore))
 else:
  target=root/'backups'/('snapshot-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));manifest=backup(root,state,target);print(json.dumps(dict(path=str(target),files=len(manifest))))
