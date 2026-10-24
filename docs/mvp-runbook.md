# Mobiel AI-commandocentrum — actuele uitvoering

Actuele taakzichtbaarheid 2026-10-23: zie
[reparatie, livebewijs en onderhoudsstap](mindmaps/task-visibility-20261023/report.md).
Iedere start_task heeft een eigen neutrale Workflow-taaknode zonder verplichte
projectbinding. Nieuwe brokerlogica en kortere publicatietick wachten op een
rustige onderhoudsherstart; herstart nooit vanuit zijn eigen lopende worker.

Status gecontroleerd op 2026-10-21 UTC op server5. Dit runbook en de actuele
AGENTS.md vervangen oudere planning-only- en Bubblewrap-releasevoorwaarden.

## Werkende keten

Telefoon/laptop met Tailscale → https://server5.taile88688.ts.net → private
Tailscale Serve → HTTP 127.0.0.1:8795 → Python-webchat/SQLite-taakbroker.
De bestaande broker is ingericht om één Codex-worker tegelijk uit te voeren.
Op verzoek van de eigenaar is tijdens deze hervatting geen Codex gestart,
ook geen nieuwe proef via de webchat. Een nieuwe opdracht via de webchat
start volgens de huidige implementatie wel een worker.

`server5-commandcenter.service` is enabled en actief als gebruiker mau.
`server5-task-backup.timer`, `server5-health.timer` en `server5-backup.timer`
zijn actief. Linger=yes; werking na een echte reboot is nog niet getest.
Geen serviceherstart, DNS-, firewall- of netwerkconfiguratie gewijzigd.

## Bewijs bij hervatting

- 11 bestaande tests geslaagd: broker/HTTP met mockworkers en herstelveiligheid.
- MVP-systemd-units slagen voor systemd-analyze verify.
- Private HTTPS-healthcheck met geldige certificaatcontrole geeft ready/server5.
- Gewone naamresolutie op server5 faalt. Met expliciete adresresolutie werkt
  dezelfde HTTPS-endpoint; dit bewijst nog geen toegang vanaf een telefoon.
- SQLite bevat drie geslaagde taken en geen queued/running-taken.
- Bestaande inventory/mvp-local-acceptance.json registreert een eerdere echte
  Codex-proef als passed; die proef is nu niet herhaald.
- Bestaande inventory/mvp-private-acceptance.json registreert eerdere lokale
  HTTPS-acceptatie. Mobiele acceptatie blijft afzonderlijk te bevestigen.

Herhaalbare HTTPS-controle zonder lokale DNS-wijziging:

```bash
curl --noproxy '*' --resolve server5.taile88688.ts.net:443:100.105.198.39 \
  --fail --silent --show-error --max-time 15 \
  https://server5.taile88688.ts.net/api/health
```

## Eerstvolgende acceptatie: telefoon

1. Verbind de telefoon met het bestaande tailnet via Tailscale.
2. Open https://server5.taile88688.ts.net en controleer het aanmeldscherm.
3. Toon uitsluitend in je eigen server5-terminal de toegangscode:
   `python3 web/commandcenter.py password`. Deel deze niet in chat of Notion.
4. Meld aan en controleer of de drie bestaande taken zichtbaar zijn.
5. Verstuur nog geen nieuwe taak zolang de instructie geldt om vanuit deze
   Codex-sessie geen nieuwe Codex-worker te starten.

## Data, beheer en herstel

Taakdatabase en lokale authenticatie staan onder
`~/.local/state/server5-commandcenter/mvp/`, buiten Git.
Dagelijkse taakbackups staan onder
`~/.local/share/server5-commandcenter/mvp-backups/`; login-sessies worden uit
de backup verwijderd. Backups op dezelfde SSD zijn geen externe rampenbackup.
Een bestaande consistente SQLite-backup wordt door de tests gevalideerd;
een productieherstel is tijdens deze hervatting niet uitgevoerd.

Controleer diensten met `systemctl --user status server5-commandcenter.service`
en logs met `journalctl --user -u server5-commandcenter.service`.
Stoppen kan met `systemctl --user stop server5-commandcenter.service`;
eerder uitgevoerde taakwijzigingen blijven bestaan. Brokerherstart markeert
lopende taken als interrupted en herhaalt deze niet automatisch.
Wachtende taken blijven wel uitvoerbaar na herstart; controleer de wachtrij
voordat je de dienst opnieuw start.

De workerconfiguratie gebruikt danger-full-access zonder technische
hostisolatie. Webopdrachten zijn lokale uitvoeringsopdrachten van de eigenaar.
Externe systemen en onomkeerbare vernietiging blijven apart geautoriseerd.
LAN-SSH blijft het herstelpad. Geen Funnel of publieke interface ingericht.

## Open werk

Telefoonacceptatie, rebootacceptatie, beoordeling/vastlegging van de bestaande
ongecommitte MVP-bestanden en een actuele Notion-snapshot/MindMap-update.
Die externe documentatie is bij deze hervattingscontrole nog niet bijgewerkt.
Historische plannen blijven als auditspoor bestaan.

Wijziging bij hervatting: uitsluitend dit runbook toegevoegd om runtimebewijs
en resterende acceptatie te scheiden. Rollback: dit document verwijderen of
gericht terugdraaien; de runtime is hierdoor niet gewijzigd.

## MCP-leestools — 2026-10-21

`list_tasks`, `task_logs` en `server_health` zijn na 96 geslaagde tests
geactiveerd naast de drie bestaande tools. Logs bevatten alleen vaste labels;
health leest uitsluitend de bestaande snapshot met expliciete staleness.
Zie [uitvoeringsverslag](mcp-reads-phase1.md) voor exacte bestanden, livebewijs,
budgetten, backupdekking, beperkingen en rollback. Direct reads blokkeren:
`touch ~/.local/state/server5-commandcenter/mvp/mcp-reads.disabled`.
ChatGPT-toolmetadata moet door de eigenaar worden ververst; zes tools verwacht.


### Hervattingscontrole 2026-10-21 16:54 UTC

De aantallen/taken en herstartuitspraken in “Bewijs bij hervatting” hierboven
zijn historisch MVP-bewijs, geen actuele taakmeting. Actueel: 96 tests opnieuw
OK, gerichte zes-tools-tunneltest OK, live zes tools en alle reads OK;
authenticatie, bestaande tunnel en private HTTPS-health OK. Geen herstart nodig:
--enable-read-tools stond al actief. Bestaande verbinding/configuratie behouden.
Zie het [aanvullende bewijs](mcp-reads-phase1.md) en de rollback daar.
ChatGPT-refresh/herverbinding blijft een eigenaarhandeling; serverdiscovery
bewijst nog geen vernieuwde toolcatalogus in een bestaande ChatGPT-chat.
Een broker-timeout kan failed geven met exit_code 0; controleer status én
resultaat en herhaal een muterende opdracht niet automatisch.

### Volgende MCP-uitbreiding 2026-10-21

Zie [uitvoering en rollback](mcp-extension-2026-10-21.md): vijf extra reads,
verwacht11 tools na adapteractivering. read_file biedt uitsluitend hash-goedgekeurde
versies van vier vaste document-IDs; documentwijziging blokkeert tot lokale review.
Task_progress bevat geen heartbeat. Git toont alleen tracked-aantallen;
backup_status geeft geen restoregarantie. Testsnapshot lokaal vernieuwen met
MCP-venv-python scripts/record-mcp-tests.py. Cancel_task is geïmplementeerd maar
uit tot veilig brokeronderhoud en eigenaaracceptatie van de webbevestiging.
Direct alleen vijf nieuwe reads blokkeren: mcp-extended.disabled in MVP-state.

Definitief17:28 UTC: activering voltooid, exact11 tools live; 112 tests OK,
live MCP/auth/tunnel en private HTTPS OK. Alleen adapter herstart. Cancel blijft
uit; huidige broker/worker behouden. Gerichte releasebackup hersteld/getest.

## Afronding zonder productieactivatie — 2026-10-21

Actuele resterende stappen en toestemmingsgrenzen: zie het
[voorbereidingsplan van 20:52 UTC](resterende-afronding-plan-2026-10-21.md).
Dit bevat de nieuwe read-only firmwarestatus en 47 gerichte sandboxtests;
productieactivering en externe backup blijven niet uitgevoerd.

Zie [vijfstappenverslag](afronding-vijf-stappen-2026-10-21.md) voor de voorbereide
single-file releaseguard (status prepared, niet armed), 450s-validatie en het
activatie-/rollbackplan. De guard herstelt uitsluitend bron op schijf; live MCP-
rollback vereist apart geautoriseerde herstart. Pending-units zijn niet geladen.
Hetzelfde verslag beschrijft de geblokkeerde root-loggingactie voor fwupd,
backupdekking en lokale encryptievoorbereiding zonder extern transport.

## Mindmap-taaklevenscyclus — 2026-10-22

[Implementatie, echte ketentest, exacte delta en rollback](mindmaps/live-lifecycle-2026-10-22.md).
Transactionele brokeroutbox en veilige kaartpublicatie zijn gebouwd en met één
échte Codex-worker bewezen tegen productie-Markdown/build/HTTP, met geïsoleerde
taakdatabase. **De actieve productiebroker heeft deze code nog niet geladen.**
Herstart is bewust niet uitgevoerd omdat de uitvoerende eigenaaropdracht een
kindproces van die service is. Na de lopende worker is één rustige brokerherstart
nodig; de nieuwe health-marker is `mindmap_lifecycle: outbox-v1`. Geen live
productieautomatisering claimen voordat activering en nieuwe taakobservatie kloppen.

### Bewijsgebonden projectafsluiting

Afsluitregels staan in `docs/mindmaps/project-closures.json`, uitsluitend opgesteld
binnen expliciet geautoriseerde eigenaaropdrachten. Lifecycle-publicatie verwerkt
deze vóór de normale build: stabiele project-/stap-ID, exacte preimage en
hashgebonden acceptatie plus terminalreceipt zijn vereist. Task succeeded alleen
is geen project finished. Volledige afsluiting vereist apart projectacceptatiebewijs.
Details, gerichte regressie, huidige activeringsstatus en rollback:
[mindmaps/projectclosure-20261022-001.md](mindmaps/projectclosure-20261022-001.md).
De kaartcorrectie is gepubliceerd; nieuwe Python-afsluitlogica vereist nog laden
van de broker na workerexit. Geen herstart vanuit de eigen worker.

## Workflowherstel 2026-10-22 — eigenaarterminal buiten brokerwachtrij

Actueel bewijs en rollback: [rapport](mindmaps/workflow-repair-20261022/report.md),
taak `server5_unblock_publish_20261022_001`. Alleen Server5, bestaande gegevens
behouden. De nieuwe dispatcher is pas actief na de veilige post-worker-herstart.

Credentialvrij status/publicatieherstel, onafhankelijk van web/MCP/workerqueue:

```bash
cd /home/mau/server5-commandcenter
python3 scripts/mindmap-rescue.py status
python3 scripts/mindmap-rescue.py drain
# Alleen na oorzaakherstel, voor één specifiek uitgeput event:
python3 scripts/mindmap-rescue.py rearm --seq 39
python3 scripts/mindmap-rescue.py drain
```

`rearm` heractiveert uitsluitend metadatapublicatie, nooit de Codex-taak.
Gebruik het actuele geblokkeerde seq, geen delivered event. Vijf automatische
pogingen per event, daarna expliciet eigenaarherstel; alle events blijven staan.
Een uitgeput head-event houdt latere publicaties vast om statusregressie te
voorkomen. Bronconflict/unknown children vereist review; nooit blind verwijderen.

### Eenmalige post-worker-herstart

Niet vanuit de lopende worker. Eigenaar wacht op terminalstatus van bovenstaande
taak. Via `status`: nul queued/running en verwachte terminalstatus/exitcode;
controleer tevens dat geen Codex-proces meer bij deze broker hoort. Zorg dat geen
andere inzender taken plaatst gedurende onderhoud. Bij twijfel niet stoppen.
Daarna in eigen Server5-terminal:

```bash
systemctl --user restart server5-commandcenter.service
curl --fail --silent --show-error --max-time 5 http://127.0.0.1:8795/api/health
python3 scripts/mindmap-rescue.py status
python3 scripts/mindmap-rescue.py drain
```

Controleer lokaal journal: nieuwe `Mindmap seq=... delivered` of een begrensde
foutpoging met seq; geen workerherhaling. Health alleen bewijst geen nieuwe code;
controleer starttijd en publicatiegedrag bij het eerstvolgende echte event.
Geen nieuwe proefopdracht nodig. Bij storing bronpreimages gericht terugzetten
volgens rapport; uitsluitend na idle opnieuw starten.

### Broker geheel defect: foreground CLI als noodpad

Bestaande LAN-SSH/eigen lokale terminal blijft buiten web/broker beschikbaar.
Geen netwerk- of SSH-wijziging nodig. Eerst `status`; draai nooit een tweede worker.
Bij onbekende/running status: eerst bestaande worker en resultaat reconstrueren,
geen automatische replay. Dit is de concrete blocker zolang een worker actief is.
Wanneer alle taken terminal zijn, geen worker meer draait en eigenaar de
herstelopdracht heeft bepaald: stop de broker in die terminal. Controleer dat de
service inactive is. Gebruik vervolgens de bestaande Codex-login via normale CLI
zonder authbestanden te openen of te kopiëren. Bijvoorbeeld voor een nieuwe,
expliciete lokale diagnose (geen herhaling van eerdere repair-taken):

```bash
systemctl --user stop server5-commandcenter.service
flock -n /home/mau/.local/state/server5-commandcenter/mvp/broker.lock \
  codex exec --ignore-user-config --disable apps --disable plugins --disable remote_plugin \
  -c 'approval_policy="never"' -c 'web_search="disabled"' \
  --sandbox danger-full-access --ephemeral -C /home/mau/server5-commandcenter - <<'PROMPT'
Lees /home/mau/AGENTS.md en project-AGENTS.md. Werk uitsluitend op Server5.
Geen externe systemen, secrets, netwerk/SSH-wijzigingen of gegevensvernietiging.
Geen achtergrondprocessen, brokerherstart, tweede worker of eerdere taakreplay.
Eigenaaropdracht NOOD-DIAGNOSE: controleer uitsluitend lokale brokercode en
metadata met scripts/mindmap-rescue.py status. Registreer bevindingen, bewijs en
voorgesteld herstel met deze lokale taak-ID; voer nog geen ander herstel uit.
PROMPT
```

`flock` voorkomt dat de broker tijdens de foreground-noodworker start; het is
geen sandbox. Houd resultaten lokaal, publiceer geen secrets. Deze route is
concreet gedocumenteerd maar nu niet gestart/getest wegens actieve worker.
Na afronding en hercontrole van idle kan eigenaar de broker weer starten met
`systemctl --user start server5-commandcenter.service` en health/drain controleren.
Geen automatische aanpassing van running/interrupted of wachtrijgegevens.


## Duurzame tweerichtingsbeslisroute — 2026-10-22

Serverkant en geïsoleerde simulatie gereed; activering wacht op veilig onderhoud zonder actieve worker. Zie [implementatie, trigger, live-handoff en rollback](decision-mvp/README.md). Gewone ChatGPT-chats worden niet gepusht of automatisch geactiveerd.

### Autonome laag-risico beslisbrug (uitgeschakeld)

MVP en offline bewijs: [ai-bridge/report.md](ai-bridge/report.md). Exacte eigenaarallowlist, begrensde dispatcher, nul betaalde API-kosten; providerautorisatie ontbreekt, productie uit. Geen service/poller gestart.

### Ollama-proef 2026-10-23

Lokale CPU-provider geïnstalleerd en ask/dispatch/wait technisch bewezen. Eén klein model gaf een inhoudelijk fout antwoord; dispatcher blijft uit, geen automatische beslisacceptatie. Service alleen loopback, niet boot-enabled. Status, bewijs en uitsluitend nieuwe onderdelen betreffende verwijdercommando’s: [installatieverslag](ai-bridge/ollama-install-20261023-002/report.md).

### Koerswijziging 2026-10-23 — Ollama-proef beëindigd

Ollama-runtime, beide qwen2.5-proefmodellen, eigen user-unit en testconfig verwijderd; historische proefverslagen hierboven zijn geen actuele runtimebeschrijving meer. Bestaande Commandcenter/MCP-diensten bleven actief. Gekozen onderzoeksvoorstel: bestaande Codex-worker met concreet productcontract en duurzame checkpoints; productbrede vervolgregelaar nog niet geïmplementeerd. Verwijderbewijs, één gezondheidscontrole, beperkingen/ChatGPT Work-vergelijking en rollback: [rapport](ai-bridge/cleanup-autonomy-20261023/report.md).


### Begrensde projectcontinuatie — 2026-10-23

Lokale uitbreiding aanwezig, **niet live geactiveerd / acceptatie geblokkeerd** door Codex-capaciteitsfout vóór testmutaties. Geen automatische retry of serviceherstart. Bestaande workerlimiet blijft 900s. Contract, bewijs, grenzen en rollback: [projectcontinuatierapport](autonomy/report.md).

### Gerichte heracceptatie autonome voortzetting — 2026-10-23

Twee echte Codex-etappes automatisch geslaagd via bestaande Store/Worker; project completed. Productiewebbroker draait nog oudere code; LIVE-activering geblokkeerd totdat na terminalreceipt/lege queue veilig vanuit host herstart kan worden. Geen zelfherstart of poller. [Bewijs, RCCAP en rollback](autonomy/acceptance-retry-20261023/report.md).

### TEST PROJECTS naar bestaande Codex-worker — 2026-10-23

Implementatie gereed, activering en echte E2E **geblokkeerd** tot één onafhankelijke
brokerherstart na terminalstatus van de actieve worker. Geen zelfherstart.
Aparte Test Projects-routing houdt Current Projects buiten deze nieuwe flow.
[Exacte herstart, eigenaarklik/bestandsproef, bewijs en rollback](test-projects/mindmap-to-queue-resume-20261023/report.md).

Current Projects opnieuw leeg en organisch ingericht (162 → 0); viewer live, nieuwe broker-lifecycle wacht op veilige herstart na de worker. Expliciete routing en rollback: [resetrapport](mindmaps/current-projects-reset-20261023.md).

### Autonome Current Projects-uitvoering — 2026-10-24

Minimale Current-only policy en workerinstructie gebouwd; **pending activation**.
Planning eerst gepubliceerd; onafhankelijke stappen naast rode menselijke review
uitvoerbaar; geen taskreplay toegevoegd. Eén representatieve controle en bestaande
Test Projects-regressie geslaagd. [Bewijs, onafhankelijke activatie en rollback](mindmaps/autonomous-execution-20261024/report.md).
