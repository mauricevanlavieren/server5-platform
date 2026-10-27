from pathlib import Path
import subprocess,json
p=Path(__file__).parent
s=json.loads((p/'live-reference.json').read_text());s['operations']['work_patterns'].pop('Noor',None);s['operations']['work_patterns'].pop('Lina',None);(p/'test-state.json').write_text(json.dumps(s))
(p/'step-reconciliation.jsonl').write_text('')
results=[]
for script in ['browser-operations.cjs','browser-extra.cjs','browser-archive.cjs']:
 r=subprocess.run(['node',script],cwd=p,text=True,capture_output=True);results.append(dict(script=script,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr));(p/'acceptance-results.json').write_text(json.dumps(results,indent=2));print(r.stdout,flush=True)
 if r.returncode:print(r.stderr,flush=True);raise SystemExit(r.returncode)
subprocess.run(['python3','export-check.py'],cwd=p,check=True)
