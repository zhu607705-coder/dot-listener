"""Start a real loopback server; test synthetic ingestion/replay/read/delete.
This does not connect a phone, microphone, external server or dot account.
"""
from pathlib import Path
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import httpx
from cryptography.fernet import Fernet

root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    env={**os.environ, 'DL_DB_PATH':str(Path(tmp)/'http.sqlite3'),
         'DL_INGEST_TOKEN':secrets.token_urlsafe(36),'DL_READ_TOKEN':secrets.token_urlsafe(36),
         'DL_ADMIN_TOKEN':secrets.token_urlsafe(36),'DL_FERNET_KEY':Fernet.generate_key().decode()}
    process=subprocess.Popen([sys.executable,'-m','uvicorn','dot_listener.app:create_app','--factory',
        '--host','127.0.0.1','--port',str(port),'--no-access-log'],env=env,
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    checks=[]
    try:
        with httpx.Client(base_url=f'http://127.0.0.1:{port}',trust_env=False,timeout=5) as client:
            for _ in range(100):
                if process.poll() is not None: raise RuntimeError('Server exited during startup')
                try:
                    if client.get('/healthz').status_code==200: break
                except httpx.TransportError: pass
                time.sleep(.05)
            else: raise TimeoutError('Loopback server failed to start')
            checks.append('real uvicorn server starts on loopback')
            fragment=json.loads((root/'examples/fragment.json').read_text())
            headers={k:{'Authorization':'Bearer '+env['DL_'+k.upper()+'_TOKEN']} for k in ['ingest','read','admin']}
            r=client.post('/v1/fragments',json=fragment,headers=headers['ingest']);r.raise_for_status()
            assert r.json()['stored'] is True and r.json()['dot_delivery']=='not_implemented'
            checks.append('HTTP ingestion returns honest receipt')
            r=client.post('/v1/fragments',json=fragment,headers=headers['ingest']);r.raise_for_status()
            assert r.json()['duplicate'] is True;checks.append('HTTP replay is idempotent')
            path='/v1/fragments/'+fragment['id']
            r=client.get(path,headers=headers['read']);r.raise_for_status()
            assert r.json()['fragment']['text']==fragment['text'];checks.append('HTTP original text round trip')
            assert client.delete(path,headers=headers['read']).status_code==403;checks.append('HTTP reader cannot delete')
            client.delete(path,headers=headers['admin']).raise_for_status()
            assert client.post('/v1/fragments',json=fragment,headers=headers['ingest']).status_code==410
            checks.append('HTTP deleted ID cannot be resurrected')
        print(json.dumps({'surface':'real localhost HTTP; synthetic input; no dot',
                          'checks_passed':len(checks),'checks':checks},ensure_ascii=False,indent=2))
    finally:
        process.terminate()
        try: process.wait(timeout=5)
        except subprocess.TimeoutExpired: process.kill();process.wait()
