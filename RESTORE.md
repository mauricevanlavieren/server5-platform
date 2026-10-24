# Server5 herstellen op vervangende Ubuntu-server

Status 24-10-2026: lokaal herstelpakket; NIET extern veiliggesteld. Deze Git-repository
heeft geen remote. Een clone-URL en remote-commitbewijs ontbreken. Dit is dus nog
geen bewezen rampenherstel. Geen migratie, installatie of serviceherstart uitgevoerd.

## Vereisten

Ubuntu 24.04 amd64, gebruiker mau met /home/mau, Python 3.12 + venv/pip,
Git, Node 22.23.3/npm, Codex CLI 0.163.0, Tailscale en de bestaande
OpenAI Secure MCP tunnel-client. Dependencydownloads en accounts blijven nodig;
Git alleen is geen offline installatiepakket. Alleen eigenaar voert onderstaande
stappen uit op de vervanger na uitval, met hersteltoegang via lokale console/SSH.
Neem hostname server5 pas over nadat het oude apparaat buiten gebruik is.

## Herstelvolgorde

1. Vul de bestaande, door eigenaar aangewezen GitHub-clone-URL en bewezen commit in.
   `git clone <BESTAANDE-URL> /home/mau/server5-commandcenter`, daarna
   `cd /home/mau/server5-commandcenter && git checkout <BEWEZEN-COMMIT>`.
   Deze twee waarden ontbreken momenteel: niet gokken en geen nieuwe repo maken.
2. Installeer op de vervanger de vereisten uit de vorige sectie via hun officiële
   distributie. Plaats Node/Codex op de PATH uit
   `systemd/user/server5-commandcenter.service` of pas die PATH aan de vervanger aan.
   Maak de MCP-omgeving:
   `python3 -m venv /home/mau/.local/share/server5-commandcenter/mcp-venv` en
   `/home/mau/.local/share/server5-commandcenter/mcp-venv/bin/pip install -r requirements-mcp.lock`.
   De precieze huidige tunnel-clientbinary staat NIET in Git: eigenaar moet die
   via de officiële bestaande distributie opnieuw beschikbaar maken.
3. Kopieer `docs/host-AGENTS.md` naar `/home/mau/AGENTS.md` na lokale review;
   project-AGENTS.md en de worker-RULES in web/commandcenter.py blijven samen leidend.
   Voer `codex login` interactief uit; kopieer geen authbestand naar Git.
4. Herstel private toestand vanuit een afzonderlijke, consistente veilige backup:
   `~/.local/state/server5-commandcenter/mvp/` (tasks.sqlite3, decisions.sqlite3,
   taaklogs, projectbindingen en overige toestand),
   `docs/mindmaps/` (histories, bindings, imports, bewijs), en
   `mindmap/public/*.json` (Current/Test Projects en legacy map).
   Bewaar huidige used_ids/history en gebruik geen oude kaart bovenop een nieuwere DB.
   Geen losse actieve SQLite-file kopiëren: gebruik bestaande consistente backups
   in `~/.local/share/server5-commandcenter/mvp-backups/`.
   Zonder zo'n afzonderlijke backup zijn deze gegevens verloren; Git bevat alleen code.
   Voor een LEGE vervanger zonder historie, vóór starten:
   `mkdir -p docs/mindmaps/current-projects docs/mindmaps/live-lifecycle docs/test-projects`;
   maak mindmap/public/current-projects.json met
   `{"used_ids":["CURRENT-PROJECTS"],"root":{"id":"CURRENT-PROJECTS","title":"Current Projects","status":"pending","children":[]}}`.
   `python3 scripts/test-projects.py init` maakt de fictieve testkaart aan.
   Legacy map/imports zijn alleen uit de afzonderlijke backup te reconstrueren;
   zonder die backup zijn legacy functies/de build geen exacte reproductie.
5. Stel privé opnieuw in, zonder waarden in Git/chat: Codex-login;
   `~/.config/server5-commandcenter/mcp-token`, tunnel-runtime-key,
   mcp-authorization-header en tunnel.yaml. Gebruik het bestaande tunnelprofiel en
   `config/tunnel-client/server5.yaml.example` als structuur. Header moet overeenkomen
   met MCP-token. Vereist bestaande tunnel-ID en beperkte Tunnels Read/Use-credential.
   Bestanden mode 0600, privédirectory 0700. De oorspronkelijke waarden zijn niet gelezen.
   Weblogin wordt lokaal opnieuw gegenereerd door de bestaande webservice;
   bestaande sessies niet herstellen als geldige toegang.
6. Corrigeer machinebindingen: /home/mau-paden, Node-PATH, hostname,
   LAN-adres in mindmap/serve.py (nu 192.168.1.245:8788), Tailscale-identiteit,
   DNS/private HTTPS-oorsprong en tunnel-clientpad. Houd 8795/8796/8797 op loopback.
   De mindmap bindt alleen op het bedoelde private LAN-adres. Geen publieke interface.
   `cd mindmap && npm ci` is alleen nodig bij herbouwen; de gebundelde browser-JS
   is onderdeel van het pakket. Herbouw van legacy maps vereist de imports uit backup.
7. Kopieer de bestaande `systemd/user/server5-*.service` en `*.timer` naar
   `~/.config/systemd/user/`, voer `systemctl --user daemon-reload` uit.
   Controleer lokale unitpaden en `systemd-analyze --user verify` voor deze bestanden.
   Controleer herstelde wachtrij VOOR starten: oude queued taken niet onbedoeld uitvoeren.
   Activeer op de vervanger pas daarna commandcenter, mcp en mindmap met
   `systemctl --user enable --now server5-commandcenter.service server5-mcp.service server5-mindmap.service`.
   Herstel bestaande health/backup/task-backup timers met
   `systemctl --user enable --now server5-health.timer server5-backup.timer server5-task-backup.timer`.
   Voor starten zonder login: eigenaar voert `sudo loginctl enable-linger mau` uit.
8. Meld de vervanger als eigenaar aan bij het bestaande tailnet. Herstel private
   Serve-config naar http://127.0.0.1:8795 en de toegestane HTTPS-origin op basis van
   de nieuwe tailnet-identiteit; raadpleeg scripts/connect-private-access.sh.
   Activeer server5-mcp-tunnel.service pas na private provisioning en nadat
   het oude apparaat geen verbinding meer maakt. ChatGPT-connector zo nodig handmatig
   opnieuw koppelen. Geen router/switch of andere server wijzigen.
9. Controleer `curl --fail http://127.0.0.1:8795/api/health`, private HTTPS-login,
   mindmap op het nieuwe LAN-adres, MCP-discovery via de bestaande connector en één
   expliciet toegestane testtaak. Verifieer Current Projects met
   web.mcp_mindmap.snapshot(ROOT): consistent=true, gelijke hashes,
   project_invariants_valid=true; iedere done-node moet een blad zijn.
   Controleer systemctl --user status voor de genoemde units. Dit herstel is tijdens
   deze taak niet op een vervanger uitgevoerd en reboot/mobile acceptatie niet bewezen.

## Buiten Git en beperkingen

Geen Git-herstel van accounts, Codex-auth, SSH-hostsleutels/gebruikerstoegang,
Tailscale-nodekeys/Serve-status, tunnelkeys/registratie, webauth/sessies,
SQLite-taakgeschiedenis/besluiten/logs, mindmapgeschiedenis/bewijs, lokale backups,
Codex skills/config, persoonlijke MCP-connectors, of eventueel lokale Ollama-modellen
(ai-dispatcher is optioneel). Niet-geheime dispatcher-template staat in config/.
Bestaande backups op dezelfde Server5-schijf overleven schijfverlies niet.
Dit pakket beschermt de commandcenteromgeving, niet alle inhoud van de host of
andere servers. Gepubliceerde broncode op GitHub kon zonder remote niet worden bevestigd.

## Rollback

Deze taak heeft geen draaiende configuratie, service of netwerk veranderd.
Lokaal pakket terugnemen via een gerichte revert van de herstelcommit; bewaar
vooraf bestaande werkboomwijzigingen en mindmap-audit. Geen git reset --hard/clean.
Op de vervanger: stop de nieuw geactiveerde units en herstel de vorige private
config uit eigen backup. Behoud console/SSH; voer geen netwerkreset uit.
