from pathlib import Path
import json
from secure_app import create_app
from demo_story import standard
p=Path('/tmp/server5-story-test-state');p.mkdir(mode=0o700,exist_ok=True);(p/'workflow.json').write_text(json.dumps(standard(1,dict(id=None,username='Fictieve demo-inrichting',role='system'))))
a=create_app(p)
for name,role,employee in [('test-owner','owner',''),('test-bram','mechanic','Bram'),('test-shop','shop',''),('test-admin','administration','')]:
 try:a.accounts.create(dict(username=name,password='Fictief-test-wachtwoord-2026',role=role,employee=employee))
 except ValueError:pass
(p/'owner-activation').unlink(missing_ok=True);print('Fresh isolated standard demo prepared')
