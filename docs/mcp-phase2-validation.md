# Fase 2 — runtimeacceptatie en activatie, 2026-10-21

Vervolg op docs/mcp-phase2.md na melding van de eigenaar dat de privéconfiguratie
gereed is. Alleen server5 gewijzigd; geen Platform-tunnel of ChatGPT-plugin
aangemaakt/gewijzigd, geen modelaanroep of echte Codex-opdracht uitgevoerd.

## Configuratie en herstelpunt

Implementatieplan en fase-2-verslag eerst uit Notion gelezen. Host server5 en
bestaande ongecommitte Git-status bevestigd. Herstelpunt vóór tests:
`~/.local/share/server5-commandcenter/phase2-backups/validation-20261021-122443/`.
Projectarchief, hashes, dienst-PIDs, Serve en consistente SQLite-kopie;
integrity_check=ok en login-sessies uit backup verwijderd. Geen credentials
gekopieerd. Lokale SSD-kopie, geen externe disaster recovery.

Profiel, runtimekey, headerfile en MCP-token: gewone bestanden, eigenaar mau,
mode 0600, geen symlinks; directory privé. Profiel exact gelijk aan het gereviewde
sjabloon met een geldig tunnel-ID ingevuld. Target blijft uitsluitend
http://127.0.0.1:8796/mcp, control plane https://api.openai.com, health loopback.
Headerfile past bij bestaand MCP-token. Geen credentialwaarden getoond.

GET van het bekende tunnelrecord via Platform geeft HTTP 200, naam
Server5 Commandcenter en een niet-lege workspacekoppeling. Read en Use zijn
functioneel aangetoond door recordlezen en succesvolle polling. Dat bewijst niet
zelfstandig dat de key géén overige rechten bezit; de restricted instelling is
door de eigenaar bevestigd bij provisioning. Geen sleutelrechten of billing
gewijzigd en geen alternatieve/admin-key gebruikt.

## Doctor: verklaarde diagnosebeperking

Officiële client 0.0.16 doctor --json --explain: exit 2, uitsluitend oauth_metadata
faalt. Profiel, tunnel-ID, keyconfiguratie en target laden wel. Doctor maakt in
cmd/client/doctor_command.go een eigen HTTP-client zonder de geconfigureerde
MCP extra/discovery headers. Daardoor ontvangt deze diagnose terecht 401 van
de afgeschermde adapter en probeert de foutbody als OAuth-metadata te lezen.

Dit is geen geslaagde doctor-run en ook geen bewijs van ongeldige runtime-auth.
De echte runtime gebruikt de ingestelde headers, initialiseert MCP en krijgt
voor niet-bestaande OAuth-metadata 404. De runtime kwalificeert OAuth als
not_advertised, status ok, en geeft /readyz HTTP 200. De generieke warning
“OAuth discovery failed” blijft zichtbaar maar blokkeert die runtime niet.

De officiële connectorhandleiding accepteert readyz=200 of een verklaarde
verwachte authenticatiechallenge als startpunt voor producttests. Op basis van
de daadwerkelijke runtime-, authenticatie- en herstelproeven is de dienst
geactiveerd. Geen auth-, Host- of Originregel verzwakt om doctor groen te maken.

Bronnen, gecontroleerd voor de geïnstalleerde release:
- https://github.com/openai/tunnel-client/blob/v0.0.16/cmd/client/doctor_command.go
- https://github.com/openai/tunnel-client/blob/v0.0.16/docs/connectors.md
- https://github.com/openai/tunnel-client/blob/v0.0.16/pkg/oauth/discovery_failure.go

## Werkelijke OpenAI-verbinding en reconnect

Met tijdelijke foreground-clients: healthz HTTP 200, readyz HTTP 200, MCP
startup_probe=succeeded, control-plane status ok, last_success gevuld en nul
consecutive_failures. Dit bewijst werkelijke geauthenticeerde tunnelpolling.

Daarna een geïsoleerde verbindingsverliesproef: alleen het tijdelijke
clientproces gebruikte een tijdelijke CONNECT-proxy op loopback. De proxy liet
uitsluitend api.openai.com:443 toe en ontsleutelde/logde geen TLS-payloads.
Na succesvolle echte polling zijn uitsluitend die testsockets verbroken en
nieuwe connecties tijdelijk geweigerd. Control-plane failures zijn waargenomen.
Na herstel hervatte hetzelfde clientproces succesvolle polling met nul fouten.
Proxy en testclient daarna gestopt. Geen firewall/netwerk/Tailscale gewijzigd.

## Binary-forwarding en authenticatie

Afzonderlijke lokale protocolfixture met de echte officiële binary, een lokale
mock-control-plane en een synthetisch credential voor die fixture. Geen echte
Platform-key naar de fixture gestuurd en geen tweede Platform-tunnel aangemaakt.
De binary gebruikte de bestaande geauthenticeerde productie-MCP-adapter.

Geslaagd via de dispatcher en response-route van de officiële binary:
- initialize met behoud van request/response-correlatie.
- tools/list retourneert exact task_status en task_result, start_task ontbreekt.
- Beide leestools op een bestaande taak; geen taakdata of resultaat gelogd.
- Meegegeven verkeerde Authorization én authorization overschrijven de statische
  header en worden werkelijk door de adapter met 401 geweigerd.
- Meegegeven browser-Origin wordt met 403 geweigerd.

Dit is echte binary-forwarding tegen een lokale mock-control-plane, geen bewijs
van een ChatGPT→OpenAI→adapter gebruikersaanroep. Dezelfde headerfile is in de
echte runtime succesvol voor de lokale MCP-startproef gebruikt.

## Productgrens en resterend werk

Een rechtstreekse test van de productgerichte /v1/mcp/{tunnel_id}-URL met de
runtimekey geeft HTTP 404. Er is geen werkende publieke SDK-aanroep op deze
route bewezen. De runtimekey is geen vervanging voor een ondersteunde
ChatGPT-productverbinding. Niet omzeild met andere keys of een Responses-model.

ChatGPT-pluginselectie/installatie is niet namens de eigenaar uitgevoerd.
Daarom blijven tools discovery en toolcalls UIT ChatGPT, telefoon en Live-spraak
afzonderlijke eigenaaracceptaties. Server-runtimeacceptatie en gebruikersacceptatie
worden niet als hetzelfde bewijs gepresenteerd.

## Systemd en regressie

Alleen server5-mcp-tunnel.service gestart en na functionele runtimeacceptatie
voor autostart geactiveerd. De nieuwe dienst is bewust met SIGKILL getest:
systemd moet automatisch herstarten en de client moet weer succesvol pollen.
Deze proef slaagde: nieuwe PID 35324, NRestarts=1, daarna opnieuw ready en
succesvolle Platform-polling. Dienst is active/enabled. Geen reboot getest.
De drie app/beheerlisteners staan uitsluitend op 127.0.0.1:8795/8796/8797.
Alle 23 bestaande tests zijn opnieuw geslaagd. Exacte credentialwaarden zijn
niet aangetroffen in het adapter-/tunneljournal of de nieuwe bronbestanden.

Bestaande webbroker PID 27844 en MCP-adapter PID 34196 ongewijzigd; geen echte
Codex-worker gestart. Alle eerdere projectbestanden vóór documentatie-updates
bytegelijk aan baseline; bestaande ongecommitte wijzigingen behouden.
Taken/events gelijk aan SQLite-herstelkopie. Tailscale Serve onveranderd.
Private HTTPS-health ready/server5, geen nieuwe publieke listener.
Taakbackup opnieuw gestart: Result=success, integrity_check=ok, nul sessies.
Drie bestaande timers actief. Bestaande fwupd-refresh-fout blijft zichtbaar;
configuratiebackup blijft vanwege de bestaande vuile Git-boom beperkt.

Reproduceerbare controles zonder secretoutput:

```bash
python3 scripts/check-tunnel-runtime.py
/home/mau/.local/share/server5-commandcenter/mcp-venv/bin/python scripts/check-mcp.py
/home/mau/.local/share/server5-commandcenter/mcp-venv/bin/python scripts/check-tunnel-local.py
systemctl --user is-active server5-mcp-tunnel.service
systemctl --user is-enabled server5-mcp-tunnel.service
```

Start_task blijft uit. Geen publieke poorten, Funnel, portforwarding, andere
servers, bestaande services, API-keyrechten of billing gewijzigd.

## Rollback

```bash
systemctl --user disable --now server5-mcp-tunnel.service
```

Dit stopt alleen de nieuwe uitgaande tunnelruntime. Laat de bestaande
Platform-tunnel, MCP-adapter, webapp, SQLite, Tailscale en backups intact.
Geen databaseherstel vereist. Bij vermoedelijke keyblootstelling laat de
eigenaar de betreffende restricted key intrekken; waarden nooit in chat delen.

## Notion

Uitvoeringsverslag: https://app.notion.com/p/400c7b03337681ffae1eebd0833967fe
Implementatieplan: https://app.notion.com/p/400c7b0333768136ba9be0a112f10b45
