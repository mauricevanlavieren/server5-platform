# Stap 1 — backupdekking en herstelbaarheid

Uitgevoerd op server5 op 2026-10-21. Alleen de backupvoorziening uitgebreid;
geen serviceherstart, reboot, credentialwijziging of netwerkconfiguratiewijziging.
De bestaande webapp, adapter, tunnel, worker, SSH en Tailscale blijven draaien.

## Oorzaak en wijziging

De oude dagelijkse configuratiebackup archiveerde alleen een schone Git HEAD.
De werkende MVP-bron/UI en enkele units waren untracked en de tree was dirty.
De oude archieven bevatten daardoor geen actuele webapp/MCP-code. De laatste
losse taakbackup bevatte zes taken, tegenover negen huidige geslaagde taken.
De oude backups zijn behouden, niet vervangen of verwijderd.

`scripts/commandcenter.py backup` maakt nu via `scripts/recovery.py` een private
herstelbundel in `~/.local/share/server5-commandcenter/backups/recovery-*.tar.gz`
met een `.tar.sha256`-sidecar. De bestaande dagelijkse usertimer roept hetzelfde
commando aan; unit, schema en timing zijn niet gewijzigd. Geen daemon-reload nodig.
De aparte bestaande taakbackup blijft daarnaast bestaan en ongewijzigd werken.

De bundel omvat:

- De actuele bytes van getrackte én niet-genegeerde untracked bronbestanden in
  web, scripts, tests, systemd, docs, plans, templates, .githooks en config, plus
  AGENTS.md, README.md, .gitignore en requirements-mcp.lock. Een vaste essentiële
  bestandenset is verplicht. Inventory, .git, caches en credentialpaden zijn uitgesloten.
- Geïnstalleerde server5-userunits als gewone bestanden, met enablementstatus,
  Linger en de daadwerkelijke host-AGENTS.md. Bekende symlinks naar dezelfde
  repositoryunit worden gecontroleerd gevolgd; geen links in het archief.
- Een SQLite online-backup met alle committed taken, resultaten en events.
  Productie wordt alleen-lezen geopend, zonder Store-initialisatie of recover.
  Login-sessies worden uitsluitend uit de kopie verwijderd, met secure_delete
  en VACUUM. De kopie gebruikt DELETE-journalmodus en is zelfstandig zonder WAL/SHM.
- De private weborigin, eventuele MCP-stopmarker en een read-only Serve-snapshot.
  Het bestaande tunnelprofiel wordt alleen opgenomen als het exact overeenkomt
  met het gereviewde file-reference-sjabloon plus bestaand tunnel-ID. Geen
  embedded keys of credentials worden overgenomen; de liveconfig blijft intact.
- Manifest: UTC, hostname, Git HEAD én dirty-status, SHA256/grootte/mode van alle
  bestanden, aantallen en volledige rij-digests van tasks/events, pakketversies,
  runtimepaden/versies/hashes en credentialrollen/bestandsrechten zonder inhoud.

Een dirty werkboom is dus niet langer een reden om alle backupdekking te verliezen.
Het manifest noemt expliciet dat de snapshot werkende bestanden bevat en niet
uitsluitend Git HEAD. Bestaand gebruikerswerk is niet blind gecommit. Wijzigingen
in de bronbestandenset of bytes tijdens de opname laten de backup veilig falen.

## Geheimen, rechten en grenzen

MCP-token, Authorization-header, Platform-runtimekey, webauth.json,
login-password, Codex-login, SSH/Tailscale-identiteit en sessies zijn niet als
credentials gekopieerd. Bekende bestaande bearer-/key-/loginwaarden worden in
het geheugen gebruikt om opname ervan te weigeren. Bronbestanden krijgen
bovendien de bestaande soorten sleutelpatrooncontroles. Dit is een heuristiek;
algemene taakinhoud blijft gevoelig en hoort alleen in private backups.

Backupdirectory en herstelmappen: 0700. Archief, checksum, manifest, data en
niet-uitvoerbare uitgepakte bestanden: 0600; uitvoerbare bronnen: 0700.
Credentialbestanden blijven ongewijzigd en zijn op eigenaar/0600 gecontroleerd.
Foutoutput van backup bevat een generieke melding, geen subprocess-stderr,
bronregels, matches, opdrachttekst, resultaten of credentials. Succesoutput toont
alleen archiefpad, Gitstatus, aantallen en verificatie-uitkomst.

Er is een lock tegen gelijktijdige nieuwe bundeljobs. Archieven worden met een
unieke naam gepubliceerd zonder bestaande snapshots te overschrijven. Geen
pruning. Het bestaande reguliere budget van 256 MiB blijft gelden: bij een vol
budget weigert de job een nieuwe snapshot en houdt alle oude exemplaren.
Per bron-/databestand en gecomprimeerde bundel geldt een bewuste grens van
16 MiB, uitpaklimiet 192 MiB. De huidige bundel/data past ruim. Dit is een
expliciete toekomstige groeigrens; falen van de job vraagt beoordeling. Er is
in deze stap geen nieuwe alarmlevering of retentiebeleid ingevoerd.

## Verificatie en herstelproef

Voor elke nieuwe backup automatisch:

1. Consistente snapshot; integrity_check en foreign_key_check.
2. Uitpakken in een nieuwe tijdelijke directory, nooit een productiepad.
3. Eerst SHA256 en alle leden valideren; traversal, absolute paden, dubbele leden,
   links, devices, te grote bestanden en afwijkende modes weigeren.
4. Exacte bestandenset, SHA256, bytes, modes en database-rij-digests vergelijken.
5. Nul sessies aantonen en alle herstelde Python-bestanden compileren zonder
   import van main, workerstart of externe verbinding.

Een aanvullende handmatige offline applicatieproef gebruikt de bestaande MCP-venv:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/commandcenter.py backup
PYTHONDONTWRITEBYTECODE=1 python3 scripts/commandcenter.py restore-test /volledig/pad/recovery-....tar.gz
PYTHONDONTWRITEBYTECODE=1 ~/.local/share/server5-commandcenter/mcp-venv/bin/python scripts/verify-recovery-app.py /volledig/pad/recovery-....tar.gz
```

De appproef pakt uit naar een nieuwe tijdelijke map, kopieert alleen de herstelde
DB naar tijdelijke state en maakt synthetische login/MCP-auth. Hij test de
herstelde HTML/JS/CSS, webhealth, authweigering, tijdelijke login en zichtbaarheid
van taken. Daarna test hij MCP-initialisatie, discovery van drie tools,
status/resultaat en authweigering. Worker.start en subprocess.Popen zijn voor
die proef geblokkeerd; geen main of echte opdracht wordt uitgevoerd. De enige
HTTP-listener is tijdelijk op loopback met een willekeurige poort. Taken/events
worden vóór/na met het manifest vergeleken. Tijdelijke proefmappen worden opgeruimd.

Uitkomsten: alle 56 tests geslaagd, waaronder 13 nieuwe herstelbundeltests en
vier bestaande herstelveiligheidstests. Negatieve tests omvatten corruptie,
manifestfraude, ontbrekende bron, traversal/links/devices/dubbele leden,
non-empty doelmap, ruimere credentialrechten, secretscan en vol budget. Een WAL-
commit wordt meegenomen; sessiewaarden verdwijnen ook uit de bytes van de kopie.
De herstelde app-/MCP-leestest slaagde met synthetische auth, nul workers en
ongewijzigde task/eventinhoud. Negen taken en 129 events zijn vastgelegd, alle
negen succeeded; nul sessies. De bestaande dependencies komen overeen met
requirements-mcp.lock. Gemeten backup inclusief automatische restoreproef circa
0,66 seconde, maximale gemeten RSS circa 54 MiB; dit is huidige belasting,
geen algemene garantie bij grotere datasets. De bestaande jobgrenzen zijn 90s,
128 MiB, 20% CPU en 16 processen/taken; er is geen nieuwe service gestart om
resourcefalen te simuleren.

Regressiecontrole geslaagd: alle vooraf bestaande projectbestanden behalve het
bewust aangepaste backupscript zijn bytegelijk; alle vooraf bestaande backups
zijn bytegelijk. Credential-/tunnelconfiguratie en Serve-configuratie zijn
bytegelijk, en de drie applicatie-PIDs/restarttellers bleven gelijk. Private
HTTPS-health, MCP-initialisatie/discovery/lezen en echte tunnelpolling slagen.
SSH/socket, tailscaled en de bestaande drie timers zijn actief. De bekende
fwupd/healthwaarschuwing is niet aangepast.

## Wat aantoonbaar herstelbaar is

**Aangetoond:** actuele applicatiebron, geïnstalleerde units, veilige instellingen,
alle huidige taak-/resultaat-/eventgegevens en functionele web/MCP-leestoegang
kunnen op server5 uit de bundel worden gereconstrueerd in een geïsoleerde map,
met de bestaande hostruntime en nieuwe tijdelijke credentials. De controles
vereisen voor nieuwe bundels geen oude Git-objecten. Oudere Git-archieven blijven
met de oude restore-test te controleren.

**Niet aangetoond:** volledig herstel op een lege host, herstel na SSD-verlies,
productie-authenticatie, externe Codex-login of ChatGPT-productacceptatie na
herstel. Binaries/venv/OS zijn niet gekopieerd: versies, hashes en MCP-lock staan
in manifest/bron, maar herinstallatie en eigenaar-reprovisioning blijven nodig.
De kopie staat op dezelfde SSD, is private maar niet apart versleuteld, en heeft
geen externe/offline bestemming. Er is geen reboot of productieherstel gedaan.

## Handmatig productieherstel, alleen na nieuwe opdracht

1. Houd bestaande ingangen en taakindiening onder expliciete controle; herstel
   nooit over de draaiende productie. Stel eerst actuele DB/WAL en huidige
   configuratie veilig. Niets automatisch afspelen.
2. Valideer de bundel en reconstrueer naar een NIEUWE directory. Controleer manifest,
   bron/dependencyversies, geïnstalleerde units en veilige settings. Alleen expliciet
   goedgekeurde onderdelen terugplaatsen; geen SSH/Tailscale-identity herstellen
   vanuit dit archief en geen Platform-tunnel opnieuw aanmaken.
3. Eigenaar maakt opnieuw lokale web/MCP-auth aan of gebruikt zijn apart veilig
   bewaarde credentials; restricted Platform-key uitsluitend via officiële flow,
   buiten Git/logs/Notion. Bestaande Codex-login hergebruiken of eigenaar opnieuw
   laten aanmelden. Geen authbestand kopiëren vanuit .codex.
4. Reconcileer task-ID's, reeds uitgevoerde effecten en queued/running-taken vóór
   enige workerstart. Een oude queued-taak kan in werkelijkheid al uitgevoerd zijn.
   DB-herstel draait wijzigingen van uitgevoerde opdrachten niet terug.
5. Pas na aparte toestemming geselecteerde diensten activeren en de echte
   mobiele/ChatGPT-verbinding toetsen. Geen automatische taakretry.

## Rollback van deze stap

Herstel uitsluitend `scripts/commandcenter.py` uit de private baseline
`~/.local/share/server5-commandcenter/step1-recovery/20261021-134412/commandcenter.py.before`,
of draai uitsluitend de eigen backupcommit terug. De oude dagelijkse job krijgt
zijn eerdere clean-Git-gedrag terug; daardoor herleeft het oude dekkingsgat.
De nieuwe helper/test/docs mogen aanwezig blijven maar worden niet aangeroepen.
Bewaar alle oude én nieuwe backups. Geen databaseherstel, unitwijziging,
daemon-reload, netwerkactie of serviceherstart nodig voor deze rollback.

Vooraf bestaande wijzigingen/untracked bestanden blijven intact. Alleen eigen
backupscriptwijziging, twee helpers, hersteltests en dit document worden gecommit.
