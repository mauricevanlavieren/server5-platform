from pathlib import Path
import subprocess,json,os
p=Path(__file__).parent
state=json.loads((p/'live-reference.json').read_text());state['operations']['work_patterns'].pop('Noor',None);state['operations']['work_patterns'].pop('Lina',None);(p/'test-state.json').write_text(json.dumps(state))
(p/'step-reconciliation.jsonl').write_text('')
results=[]
for script in ['browser-operations.cjs','browser-extra.cjs','browser-archive.cjs','browser-journeys.cjs','browser-fixes.cjs','browser-collaboration.cjs']:
 env=dict(os.environ,DISPLAY=':97');r=subprocess.run(['node',script],cwd=p,text=True,capture_output=True,env=env)
 results.append(dict(script=script,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr));(p/'acceptance-results.json').write_text(json.dumps(results,indent=2));print(script,r.stdout,flush=True)
 if r.returncode:print(r.stderr,flush=True);raise SystemExit(r.returncode)
subprocess.run(['python3','export-check.py'],cwd=p,check=True)
(p/'acceptance-final-state.json').write_bytes((p/'test-state.json').read_bytes())
