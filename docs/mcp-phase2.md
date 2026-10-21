# Fase 2 — tunnel-client voorbereid, wacht op eigenaar

Actuele vervolgstatus: de eigenaar heeft de configuratie aangeleverd; runtime,
polling, authenticatie en reconnect zijn getest en de tunneluserdienst is actief.
Zie [runtimeacceptatie](mcp-phase2-validation.md) voor bewijs, de doctorbeperking
en de nog openstaande ChatGPT-/telefoonacceptatie. Onderstaand verslag bewaart
de oorspronkelijke voorbereidingsstatus.

Datum: 2026-10-21 UTC. Implementatieplan en fase-1-verslag eerst gelezen.
Status: officiële client geïnstalleerd; GEEN actieve OpenAI-verbinding.
Het ID van de bestaande tunnel en de restricted runtimekey ontbreken.
Conform stopconditie niet verdergegaan met doctor/netwerkactivatie.
Geen Platform- of ChatGPT-instellingen gewijzigd, geen tweede tunnel of plugin
aangemaakt, geen API-key aangemaakt, geen billing of aankoop geactiveerd.

## Herstelpunt en behoud

Voor wijzigingen: projectarchief met bestaande ongecommitte bestanden,
bestands-hashes, service-PIDs, Serve-configuratie en consistente SQLite-backup:
`~/.local/share/server5-commandcenter/phase2-backups/20261021-121226/`.
SQLite integrity_check=ok; login-sessies uit de kopie verwijderd. Lokale kopie
op dezelfde SSD, geen externe rampenbackup. Credentials zijn niet gekopieerd.

Alle pre-existente projectbestanden en taken/events na afloop gelijk aan de
baseline. Bestaande ongecommitte wijzigingen behouden. Geen bestaande dienst
herstart: webbroker PID 27844 en MCP-adapter PID 34196 bleven gelijk.

## Geïnstalleerde release

- Officiële volledige Linux-amd64 client v0.0.16.
- Uitvoer: 0.0.16+5f99daabd4aa4a77049e6d81d54a0d8c18335397.
- Archief: tunnel-client-v0.0.16-linux-amd64.zip.
- SHA256: `d60cdba019bce451bcc3a15478cc5b9cb11270b049f5b56ea39a80b517f8b117`.
- Vergeleken met de officiële SHA256SUMS.txt van dezelfde release vóór uitvoering.
  Dit is checksumverificatie; geen onafhankelijke Sigstore-attestatie uitgevoerd.
- Bewaard onder `~/.local/share/server5-commandcenter/tunnel-releases/v0.0.16/`.
- Binary via `~/.local/bin/tunnel-client`; absolute pad gebruikt door systemd.
- Alleen tunnel-client uit het archief geïnstalleerd. De meegeleverde cloudflared
  niet uitgepakt/geactiveerd. Geen Codex-plugin of assistantcommando uitgevoerd.

Release: https://github.com/openai/tunnel-client/releases/tag/v0.0.16
Checksum: https://github.com/openai/tunnel-client/releases/download/v0.0.16/SHA256SUMS.txt

## Configuratie en beveiliging

`config/tunnel-client/server5.yaml.example` bevat uitsluitend een sjabloon.
Het tunnel-ID is bewust geen fictief actief ID. Werkelijke configuratie wordt
pas na de eigenaarshandeling opgeslagen in
`~/.config/server5-commandcenter/tunnel.yaml`, mode 0600.

- Alleen target http://127.0.0.1:8796/mcp; geen stdio of tweede worker.
- Alleen bestaande task_status en task_result. start_task blijft afwezig.
- `mcp-authorization-header` aangemaakt naast het bestaande MCP-token, mode
  0600, met de volledige Bearer-headerwaarde, zonder terminaloutput.
- Zowel mcp.extra_headers als mcp.discovery_extra_headers gebruiken een
  file:-referentie. Geen secrets in profiel, unit, argv, Git of Notion.
- Platform-runtimekey krijgt een ander bestand: `tunnel-runtime-key`.
  Dit bestand bestaat nog niet. Geen bestaande OpenAI/Codex-key hergebruikt.
- Control plane vast ingesteld op https://api.openai.com. Alleen uitgaand HTTPS.
- Health/beheer later uitsluitend 127.0.0.1:8797; momenteel geen listener daar.
- Raw HTTP logging expliciet uit; waarschuwingniveau; geen payloadcapture.
- Host-, Origin- en authentificatieregels van de bestaande adapter niet gewijzigd.

De officiële releasebron en configuratiedocumentatie zijn gecontroleerd:
doorgestuurde headers overschrijven statische headers hoofdletterongevoelig.
Een onjuiste doorgestuurde Authorization mag dus 401 veroorzaken. Niet oplossen
door auth uit te zetten of willekeurige Host/Origin toe te staan. De lokale
bearer is een eigenaarcredential, geen bewijs van een ChatGPT-gebruikersidentiteit.
Tunnel/workspace/pluginrechten moeten later uitsluitend de eigenaar toelaten.

## Aparte userdienst

`systemd/user/server5-mcp-tunnel.service` is gekopieerd naar de usermanager en
gevalideerd met systemd-analyze. Status disabled/inactive; geen autostart nu.
De unit heeft ConditionPathExists voor profiel, runtimekey en lokale headerfile.

Bij latere vrijgave: Restart=on-failure, tien seconden pauze, maximaal vijf
startpogingen per vijf minuten. Schoon procesmilieu via env -i voorkomt
onbedoelde overname van bestaande API-keys/proxies/configuratievariabelen.
NoNewPrivileges, read-only home/system, private tmp, begrensd geheugen/CPU/PIDs.
Geen wijzigingen aan webapp-, adapter-, monitoring- of backupunits.

## Tests en bewijs

Geslaagd:
- Alle 23 tests geslaagd, inclusief vier nieuwe tests voor 0600-opslag,
  secretvrije uitvoer/profiel, behoud van bestaande keys en weigering bij
  ongeldig ID of onbevestigde restricted rechten. Alleen synthetische testkeys.
- SHA256 en binary --version; CLI quickstart, samples en help gelezen.
- YAML-veldnamen gecontroleerd tegen de bron van release v0.0.16.
- Officiële MCP-client: initialisatie, discovery, bestaande taakstatus/resultaat
  en weigering start_task. Geen taak ingediend.
- Headerfile 0600, geauthenticeerde tools/list geeft alleen de twee leestools.
- Lokaal gesimuleerde headeroverschrijving met verkeerde Authorization en
  authorization geeft beide 401. Onjuiste Host 421, iedere browser-Origin 403.
- Bestaande bestands-hashes, taken/events, service-PIDs en Serve ongewijzigd.
- Private HTTPS-health geeft ready/server5. Drie bestaande timers actief.
- Laatste taakbackup en configuratiebackup Result=success.

Reproduceerbare lokale checks:

```bash
/home/mau/.local/share/server5-commandcenter/mcp-venv/bin/python scripts/check-mcp.py
/home/mau/.local/share/server5-commandcenter/mcp-venv/bin/python scripts/check-tunnel-local.py
systemd-analyze --user verify systemd/user/server5-mcp-tunnel.service
```

Nog NIET getest: doctor tegen OpenAI, tunnel-ID/workspace/rechtenvalidatie,
werkelijke headerforwarding door de client, tunnelinitialisatie/discovery,
readiness, reconnect, systemd-runtime en telefoon/Live-spraak. De lokale
overschrijvingssimulatie is geen end-to-end tunnelovertest.

## Bestaande monitoring en backupbeperkingen

fwupd-refresh.service blijft failed; de hostmonitoring meldt dit met exitcode 1.
Dit was al vóór fase 1 aanwezig en is niet gerepareerd of verborgen.
Configuratiebackup vereist een schone Git-boom. Die bestaande beperking blijft
vanwege behouden ongecommitte wijzigingen. Afzonderlijk herstelpunt gemaakt;
geen brede commit of aanpassing van backupbeleid. Geen reboot uitgevoerd.

## Concrete eigenaarshandeling — hier stopt de uitvoering

1. Open bestaande tunnel Server5 Commandcenter in Platform, kopieer het bestaande
   tunnel-ID. Maak geen tweede tunnel en wijzig de workspacekoppeling niet.
2. Maak in Platform Runtime API keys een Restricted runtimekey met uitsluitend
   Tunnels Read + Use. De principal moet dezelfde rechten voor de bestaande
   tunnel hebben. Geen All, Manage of admin-key. Als beperkte rechten of toegang
   ontbreken, of Platform billing/upgrade/aankoop verlangt: stop en meld dit.
3. Voer in je eigen server5-terminal uit:

```bash
python3 /home/mau/server5-commandcenter/scripts/configure-tunnel.py
```

Het script vraagt ID en daarna de key onzichtbaar via getpass. Het weigert
niet-interactief gebruik en overschrijft geen bestaande configuratie. Het maakt
0600-bestanden en start geen verbinding of dienst. Meld uitsluitend
“configuratie gereed”; deel geen key, schermfoto of terminalinhoud.
De bevestiging van restricted rechten is een eigenaarverklaring; het script kan
de feitelijke keyrechten niet zelfstandig vaststellen. Die worden later getest.

Platform:
- https://platform.openai.com/settings/organization/tunnels
- https://platform.openai.com/settings/organization/api-keys

Een afzonderlijk tunneltarief is niet bevestigd. Geen billingwijziging uitgevoerd;
voor activatie eventuele account-/kostenvoorwaarden met de eigenaar oplossen.

## Vervolg na eigenaarshandeling

Eerst private bestandsrechten, bestaande tunnel-ID/naam en restricted rechten
controleren. Doctor --explain met profiel uitvoeren zonder secrets te printen;
daarna alleen bij veilige uitkomst de userdienst starten en health/ready toetsen.
Werkelijke Authorization-overschrijving en reconnect testen zonder taken te
starten. Geen API-modelaanroep nodig. ChatGPT-plugininstallatie blijft expliciet
een eigenaarshandeling, niet automatisch door deze agent uit te voeren.

## Rollback

De dienst draait nu niet; rollback vereist geen stop van bestaande onderdelen.
Na eventuele latere activatie uitsluitend:

```bash
systemctl --user disable --now server5-mcp-tunnel.service
```

Daarna eventueel alleen de nieuwe tunnelunit/symlink/binary en headerfile gericht
verwijderen na beoordeling. Bestaand MCP-token, MCP-service, webapp, SQLite,
Tailscale en backups behouden. Een later aangemaakte runtimekey zo nodig door
de eigenaar intrekken. Bestaande OpenAI-tunnel niet verwijderen of wijzigen.
Geen databaseherstel nodig: deze fase wijzigde geen taken of gebeurtenissen.

## Bronnen

- https://developers.openai.com/api/docs/guides/secure-mcp-tunnels
- https://github.com/openai/tunnel-client
- https://github.com/openai/tunnel-client/blob/v0.0.16/docs/configuration.md
- https://github.com/openai/tunnel-client/blob/v0.0.16/docs/permissions.md
- Implementatieplan: https://app.notion.com/p/400c7b0333768136ba9be0a112f10b45
- Fase 1: https://app.notion.com/p/400c7b033376817d929ae2db42d560dc
- Uitvoeringsverslag fase 2: https://app.notion.com/p/400c7b03337681ffae1eebd0833967fe
