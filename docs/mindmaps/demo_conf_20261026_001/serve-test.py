from pathlib import Path
import workflow,app
from http.server import ThreadingHTTPServer
workflow.FILE=Path(__file__).parent/'test-state.json'
if not workflow.FILE.exists():workflow.FILE.write_bytes((Path(__file__).parent/'live-reference.json').read_bytes())
app.STATE=Path(__file__).parent/'test-config'
ThreadingHTTPServer(('127.0.0.1',8876),app.Handler).serve_forever()
