#!/usr/bin/env python3
"""Owner's terminal-only provisioning. Never starts a tunnel or prints keys."""
import getpass
import os
from pathlib import Path
import re
import socket
import sys


def main():
    if socket.gethostname() != 'server5' or not sys.stdin.isatty():
        raise SystemExit('Voer dit uitsluitend interactief in je eigen server5-terminal uit.')
    os.umask(0o077)
    directory = Path.home() / '.config/server5-commandcenter'
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    keyfile = directory / 'tunnel-runtime-key'
    config = directory / 'tunnel.yaml'
    if keyfile.exists() or keyfile.is_symlink() or config.exists() or config.is_symlink():
        raise SystemExit('Bestaande configuratie behouden; eerst gericht beoordelen.')
    print('Gebruik uitsluitend de bestaande tunnel Server5 Commandcenter.')
    print('Maak in Platform een Restricted runtimekey met alleen Tunnels Read + Use.')
    print('Geen All, Manage, admin-key, billingactivatie of aankoop. Stop als dit niet beschikbaar is.')
    tunnel = input('ID van de bestaande tunnel (geen nieuwe tunnel maken): ').strip()
    if not re.fullmatch(r'tunnel_(?:[a-z0-9]{4}_)?[a-z0-9]{32}', tunnel):
        raise SystemExit('Ongeldig tunnel-ID; niets opgeslagen.')
    confirmation = input('Heeft deze key uitsluitend Tunnels Read + Use? Typ ja: ').strip()
    if confirmation != 'ja':
        raise SystemExit('Gestopt; beperkte rechten zijn vereist.')
    key = getpass.getpass('Plak runtimekey (onzichtbaar; nooit in chat): ').strip()
    if not re.fullmatch(r'sk-[A-Za-z0-9_-]{20,}', key):
        raise SystemExit('Ongeldig sleutelformaat; niets opgeslagen.')
    template = (Path(__file__).resolve().parents[1] / 'config/tunnel-client/server5.yaml.example').read_text()
    # Exclusive creation refuses symlinks and preserves existing credentials.
    with keyfile.open('x') as stream:
        stream.write(key + '\n')
    with config.open('x') as stream:
        stream.write(template.replace('OWNER_EXISTING_TUNNEL_ID', tunnel))
    print('Privéconfiguratie opgeslagen met mode 0600. Geen verbinding gestart.')
    print('Meld alleen: configuratie gereed. Deel geen key of terminalinhoud.')


if __name__ == '__main__':
    main()
