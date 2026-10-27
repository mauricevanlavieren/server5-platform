from pathlib import Path
import shutil,os
from secure_app import create_app
p=Path('/tmp/server5-pilot-test-state');p.mkdir(mode=0o700,exist_ok=True)
shutil.copy2('live-reference.json',p/'workflow.json')
app=create_app(p)
for username,role,employee in [('test-owner','owner',''),('test-bram','mechanic','Bram'),('test-admin','administration','')]:
 try:app.accounts.create(dict(username=username,password='Fictief-test-wachtwoord-2026',role=role,employee=employee))
 except ValueError:pass
(p/'owner-activation').unlink(missing_ok=True)
print('Isolated fictional test state prepared; no live credentials')
