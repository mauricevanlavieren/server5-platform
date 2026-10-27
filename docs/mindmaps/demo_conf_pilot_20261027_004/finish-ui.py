import json,subprocess,hashlib
from pathlib import Path
p=Path(__file__).parent;d=json.loads((p/'deployment-results.json').read_text());name='static/pilot.js'
script='CONTENT='+repr((p/name).read_text())+'\nEXPECTED='+repr(d['source_sha256'][name])+'\n'+r'''
from pathlib import Path
import hashlib,subprocess,json,shutil
root=Path('/home/mau/server4-mobile-demo');target=root/'static/pilot.js'
assert hashlib.sha256(target.read_bytes()).hexdigest()==EXPECTED,'Concurrent UI change'
saved=root/'backups/demo_conf_pilot_20261027_004/post-review/static/pilot.js';saved.parent.mkdir(parents=True,exist_ok=False);shutil.copy2(target,saved)
tmp=target.with_suffix('.js.pilot-tmp');tmp.write_text(CONTENT);tmp.replace(target)
# Static files are loaded per request; no service restart or business-state write.
snapshot=json.loads(subprocess.check_output([str(root/'.venv/bin/python'),str(root/'recovery.py')],text=True))
print(json.dumps(dict(result='PASS',file='static/pilot.js',sha256=hashlib.sha256(target.read_bytes()).hexdigest(),snapshot=snapshot),indent=2))
'''
r=subprocess.run(['ssh','-F','/dev/null','-i','/home/mau/.ssh/id_ed25519_server5_servers12','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','IdentitiesOnly=yes','-o','IdentityAgent=none','-o','HostKeyAlgorithms=ssh-ed25519','mau@192.168.1.163','python3 -'],input=script,text=True,capture_output=True)
if r.returncode:raise RuntimeError(r.stderr)
result=json.loads(r.stdout);(p/'ui-final-deployment.json').write_text(json.dumps(result,indent=2));d['snapshot']=result['snapshot'];d['source_sha256']['static/pilot.js']=result['sha256'];(p/'deployment-results.json').write_text(json.dumps(d,ensure_ascii=False,indent=2));print(r.stdout)
