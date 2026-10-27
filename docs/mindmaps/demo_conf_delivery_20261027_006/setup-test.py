from pathlib import Path
import shutil,subprocess
from secure_app import create_app
p=Path('/tmp/server5-delivery-test-state');p.mkdir(mode=0o700,exist_ok=True)
source=Path(__file__).parent/'live-reference.json'
if not source.exists():
 r=subprocess.run(['ssh','-F','/dev/null','-i','/home/mau/.ssh/id_ed25519_server5_servers12','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','IdentitiesOnly=yes','-o','IdentityAgent=none','-o','HostKeyAlgorithms=ssh-ed25519','mau@192.168.1.163','cat /home/mau/.local/state/server4-mobile-demo/workflow.json'],capture_output=True,check=True);source.write_bytes(r.stdout)
shutil.copy2(source,p/'workflow.json')
app=create_app(p)
for name,role,employee in [('test-owner','owner',''),('test-bram','mechanic','Bram'),('test-shop','shop',''),('test-admin','administration','')]:
 try:app.accounts.create(dict(username=name,password='Fictief-test-wachtwoord-2026',role=role,employee=employee))
 except ValueError:pass
(p/'owner-activation').unlink(missing_ok=True)
print('Isolated test accounts prepared')
