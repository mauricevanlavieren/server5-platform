from pathlib import Path
import tempfile,json,subprocess,sys,hashlib,urllib.request
from recovery import backup,restore
p=Path(__file__).parent
fixture=p/'acceptance-final-state.json'
if not fixture.exists():raise SystemExit('Run sequential browser acceptance first')
with tempfile.TemporaryDirectory() as tmp:
 t=Path(tmp);state=t/'original-state';state.mkdir();(state/'workflow.json').write_bytes(fixture.read_bytes());snapshot=t/'snapshot';manifest=backup(p,state,snapshot)
 app=t/'restored-app';dest=t/'restored-state';app.mkdir();dest.mkdir();(app/'app.py').write_text('BEFORE RESTORE');(dest/'workflow.json').write_text('{"preserve":"newer-state-marker"}')
 saved=Path(restore(app,dest,snapshot));assert (saved/'state/workflow.json').read_text()=='{"preserve":"newer-state-marker"}'
 assert (dest/'workflow.json').read_bytes()==fixture.read_bytes()
 for name,digest in manifest.items():
  restored=(app if name.startswith('source/') else dest)/name.split('/',1)[1];assert hashlib.sha256(restored.read_bytes()).hexdigest()==digest
 command="import workflow,app,json;from pathlib import Path;from http.server import ThreadingHTTPServer;workflow.FILE=Path("+repr(str(dest/'workflow.json'))+");app.STATE=Path("+repr(str(dest))+");server=ThreadingHTTPServer(('127.0.0.1',0),app.Handler);print(json.dumps({'port':server.server_address[1]}),flush=True);server.serve_forever()"
 child=subprocess.Popen([sys.executable,'-u','-c',command],cwd=app,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 try:
  port=json.loads(child.stdout.readline())['port'];url='http://127.0.0.1:'+str(port)
  health=json.load(urllib.request.urlopen(url+'/health'));dash=json.load(urllib.request.urlopen(url+'/api/dashboard'));view=json.load(urllib.request.urlopen(url+'/api/workflow'));export=urllib.request.urlopen(url+'/api/accounting-export').read();commercial=urllib.request.urlopen(url+'/praktijkproef').read()
  assert view['metrics']['illustration_seconds'] is None
  assert health['status']=='ok' and export and b'Nog vast te stellen' in commercial
  original=json.loads(fixture.read_text());assert view['revision']==original['revision'];assert len(view['history'])==len(original['history']);assert all(all(projected.get(k)==value for k,value in raw.items()) for projected,raw in zip(view['history'],original['history']));assert (dest/'workflow.json').read_bytes()==fixture.read_bytes()
  assert any(j.get('administrative_closed') for j in view['jobs'].values());assert view['operations']['demo_runs']==original['operations']['demo_runs']
 finally:child.terminate();child.wait(timeout=5)
 (snapshot/'source/app.py').write_text('TAMPERED');before=(dest/'workflow.json').read_bytes()
 try:restore(app,dest,snapshot)
 except ValueError:pass
 else:raise AssertionError('Tampered backup accepted')
 assert (dest/'workflow.json').read_bytes()==before
 result=dict(result='PASS',backup_files=len(manifest),restored_revision=view['revision'],restored_net_receipts_cents=dash['payments_cents'],restored_revenue_cents=dash['revenue_cents'],history_count=len(view['history']),checks=['all source/state manifest hashes','before-restore preserves newer data','restored HTTP dashboard/workflow/export/practice page','dossiers/tour rounds/history preserved','no state mutation by reads','tamper rejected before writes'],environment='isolated temporary app/state on Server5; no live restore')
 (p/'recovery-full-results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
