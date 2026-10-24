#!/usr/bin/env python3
"""Run local regression suite and atomically record only a bounded safe summary."""
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'web'))
from commandcenter import ROOT, STATE
from mcp_extended import source_version
from mcp_reads import directory_fd, utc

def main():
    if socket.gethostname() != 'server5':
        raise SystemExit('Uitsluitend server5')
    before=source_version(ROOT)
    began=time.time()
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    with tempfile.TemporaryFile() as log:
        result=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-q'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
        log.seek(0,2);size=log.tell();log.seek(max(0,size-4096));tail=log.read().decode('utf-8','replace')
    count=re.search(r'Ran (\d+) tests? in ',tail)
    after=source_version(ROOT)
    payload=dict(schema_version=1,status='passed' if result.returncode==0 and count else 'failed',
        observed_at=utc(time.time()),tests=int(count[1]) if count else 0,source_version=after,stale=before!=after,
        scope='local_unit_integration_security_regression')
    with directory_fd(STATE) as directory:
        name='mcp-test-status-'+str(os.getpid())+'.tmp'
        fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=directory)
        try:
            with os.fdopen(fd,'w') as stream:
                json.dump(payload,stream);stream.write('\n');stream.flush();os.fsync(stream.fileno())
            os.rename(name,'mcp-test-status.json',src_dir_fd=directory,dst_dir_fd=directory)
        finally:
            try:os.unlink(name,dir_fd=directory)
            except FileNotFoundError:pass
    print(json.dumps({'status':payload['status'],'tests':payload['tests'],'stale':payload['stale'],'seconds':round(time.time()-began,2)}))
    return result.returncode or int(payload['status']!='passed')
if __name__=='__main__':raise SystemExit(main())
