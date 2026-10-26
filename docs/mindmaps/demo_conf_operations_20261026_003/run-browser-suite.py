from pathlib import Path
import subprocess
root=Path(__file__).parent
(root/'test-state.json').write_bytes((root/'live-reference.json').read_bytes())
for script in ['browser-operations.cjs','browser-extra.cjs','browser-archive.cjs','visual-final.cjs']:
 print('RUN',script,flush=True);subprocess.run(['node',script],cwd=root,check=True)
subprocess.run(['python3','export-check.py'],cwd=root,check=True)
