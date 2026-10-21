#!/usr/bin/env python3
"""Inspect local tunnel health only; no secrets, model calls or task submissions."""
import json
import subprocess
import urllib.request


def main():
    with urllib.request.urlopen('http://127.0.0.1:8797/health?details=true', timeout=5) as response:
        health = json.load(response)
    assert health['live'] and health['ready'], 'Tunnel niet ready'
    cp = health['components']['control-plane']
    assert cp['status'] == 'ok' and cp['details'].get('last_success'), 'Nog geen succesvolle Platform-poll waargenomen'
    assert cp['details']['consecutive_failures'] == 0, 'Control-planeverbinding heeft fouten'
    assert health['components']['cloudflared']['state'] == 'disabled', 'Onverwachte extra transportconfiguratie'
    assert health['components']['mcp']['details']['startup_probe']['state'] == 'succeeded', 'MCP-startproef niet geslaagd'
    active = subprocess.check_output(['systemctl', '--user', 'is-active', 'server5-mcp-tunnel.service'], text=True).strip()
    assert active == 'active', 'Userdienst niet actief'
    print('Tunnel-runtime PASS: live, ready, geauthenticeerde Platform-polling en lokale MCP-startproef; geen taak gestart.')
    print('Dit bewijst geen ChatGPT-plugininstallatie of gebruikersaanroep vanuit de telefoon.')


if __name__ == '__main__':
    main()
