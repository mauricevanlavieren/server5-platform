#!/usr/bin/env python3
"""Local header safety checks only; no OpenAI requests or task submissions."""
from pathlib import Path
import stat
import httpx


def main():
    path = Path.home() / '.config/server5-commandcenter/mcp-authorization-header'
    assert not path.is_symlink()
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    value = path.read_text().strip()
    headers = {'Authorization': value, 'Accept': 'application/json, text/event-stream'}
    body = {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list', 'params': {}}
    url = 'http://127.0.0.1:8796/mcp'
    with httpx.Client(trust_env=False, timeout=5) as client:
        result = client.post(url, headers=headers, json=body)
        assert result.status_code == 200
        assert {t['name'] for t in result.json()['result']['tools']} == {'task_status', 'task_result'}
        for name in ['Authorization', 'authorization']:
            overridden = {k: v for k, v in headers.items() if k.lower() != name.lower()}
            overridden[name] = 'Bearer incorrect'
            assert client.post(url, headers=overridden, json=body).status_code == 401
        assert client.post(url, headers={**headers, 'Origin': 'https://chatgpt.com'}, json=body).status_code == 403
        assert client.post(url, headers={**headers, 'Host': 'evil.invalid'}, json=body).status_code == 421
    print('Lokale header/auth/discovery-controle PASS. Werkelijke tunnel-forwarding nog niet getest.')


if __name__ == '__main__':
    main()
