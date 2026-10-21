# Stap 2 — health-monitoring en fwupd-diagnose

Uitgevoerd op 2026-10-21, alleen server5. Verbeterplan en stap-1-verslag uit
Notion vooraf gelezen. Geen reboot, firmware-update, netwerk-/SSH-/Tailscale-
wijziging, credentialwijziging of service-uitschakeling. Alleen de lokale
hostmonitorlogica is aangepast; geen fwupd-unit of applicatieservice gewijzigd.

## Herstelpunt vóór wijzigingen

De bestaande verbeterde backup is eerst geslaagd:
`~/.local/share/server5-commandcenter/backups/recovery-20261021-135800-1792591080488654578.tar.gz`.
Negen taken en 129 events; automatische geïsoleerde restore-test passed.
Daarnaast zijn het vorige `scripts/commandcenter.py`, de health-unit en de
baseline met bestandshashes/PIDs/Serve/config-hashes privé vastgelegd onder
`~/.local/share/server5-commandcenter/step2-health/20261021-135818/`.
Bestanden 0600, directory 0700. Geen credentials gekopieerd naar deze baseline.

## 1. Werkelijke fout en grenzen van het bewijs

De oorspronkelijke `server5-health.service` crasht niet: status() maakt JSON en
retourneert bool(alerts). De bekende gefaalde systemunit fwupd-refresh veroorzaakt
daarom bewust exitcode 1. De monitor vraagt de systemmanager, niet zijn eigen
usermanager; er is geen aangetoonde zelfversterkende failed-unitlus.

Fwupd-refresh heeft werkelijk exitstatus 1. De vendorunit accepteert 2 en 101
als succes, maar onderdrukt stderr met `StandardError=null`. Daarom ontbreekt
het specifieke foutdetail van de historische servicepogingen. De optische-
stationwaarschuwing `/dev/sr0` uit het daemonjournal bewijst geen oorzaak van
de metadatafout. Er zijn geen apparaat-/sandboxrechten verruimd.

Een gerichte reproductie is uitgevoerd als bestaande gebruiker mau:

```bash
fwupdmgr refresh --json --no-authenticate
```

Dit ververst uitsluitend metadata en schakelt interactieve vragen uit. Er is
geen update/install/upgrade/firmwareactie uitgevoerd en geen `--force` of
TLS-uitschakeling gebruikt. AutomaticReports en AutomaticSecurityReports staan
in het bestaande remoteprofiel uit; niets aan deze instellingen gewijzigd.
De reproduceerbare fout kwam na circa 114,87 seconden:

- exit 1; FwupdError code 19;
- Failed to download metadata for lvfs;
- Transient failure to download, server response was 503;
- CDN/Varnish-respons: Timed out while waiting.

De uitvoer is in het geheugen van bekende credentialwaarden ontdaan en alleen
in een privédiagnosebestand vastgelegd. Het verslag bevat alleen bovenstaande
foutcategorie, geen HTTP-payload, trace-identifiers, apparaatdata of secrets.

Aanvullende GET-proeven met normale certificaatcontrole en zonder opgeslagen
responsebody: `firmware.xml.zst` gaf HTTP200, 1.993.095 bytes in circa 0,35s;
`firmware.xml.zst.jcat` gaf geen antwoord binnen twintig seconden. Een eerdere
HEAD op alleen het hoofdbestand was dus onvoldoende om de hele metadataflow
gezond te verklaren. Een afzonderlijke langere signature-proef is hieronder
bij de definitieve metingen opgenomen.

**Conclusie:** in de actuele fwupd-metadataflow is een echte upstream
HTTP503/time-out gereproduceerd. Dat is een beschikbaarheids-/onderhoudsfout,
geen onschuldige melding “geen updates”. De respons komt uit de CDN-route;
welke achterliggende CDN/origincomponent het veroorzaakt is niet vastgesteld
en valt buiten server5. De proef liep niet als UID fwupd-refresh en niet in
zijn systemd-sandbox: identieke oorzaak van iedere eerdere servicepoging is
zonder oorspronkelijk stderr-detail niet bewezen.

`sudo -n true` meldt dat een wachtwoord nodig is. Daarom geen root-drop-in
geplaatst en geen authenticatie omzeild. Directe stderr-observatie van de
originele systeemdienst blijft een eventuele eigenaarshandeling; niet nodig
om de echte fout zichtbaar te houden. Een volgende reguliere fwupd-poging mag
zelf herstellen; er is geen reset-failed of maskering toegepast.

Primaire versiebron: [fwupdmgr 2.0.20](https://github.com/fwupd/fwupd/blob/2.0.20/src/fwupdmgr.md).
De handleiding onderscheidt metadata-refresh van firmware-update. Lokale
CLI-help bevestigt dat JSON interactieve prompts uitschakelt. Geen pakket-
upgrade, firmwaredownload/installatie of externe systeemwijziging uitgevoerd;
alleen metadata en metadata-signatuur opgevraagd.

## 2. Aantoonbare monitoringtekorten en gerichte correcties

Gewijzigd: `scripts/commandcenter.py` delegeert status naar het nieuwe
`scripts/health.py`. Backup en restore van stap 1 zijn behouden. De bestaande
health-unit/timer blijven bytegelijk; geen daemon-reload of herstart nodig.
De timer heeft de nieuwe code op 14:03 UTC al regulier uitgevoerd.

### Gescheiden uitkomsten

Schema 2 bevat `errors`, `warnings`, `collector_errors`, `status` en `exit_code`.
Het bestaande `alerts` blijft aanwezig en bevat alle categorieën; waarschuwingen
verdwijnen dus niet. `failed_units` bevat nu veilige unitnamen zonder vrije
beschrijvingen of commandostderr. De actuele mislukte fwupd-refresh krijgt
`firmware_metadata_refresh_failed` als echte fout, niet een globale “unknown”.

- Exit 0: meting geslaagd en geen echte fout; status ok of warning.
- Exit 1: echte fout, zoals gefaalde unit, te weinig RAM/schijfruimte, uitgevallen
  SSH of niet-gesynchroniseerde NTP.
- Exit 2: meting onbetrouwbaar/onvolledig, zoals commando-time-out, ongeldige
  uitvoer, onleesbare resource of onschrijfbare meetopslag. Reeds bekende echte
  fouten blijven ook bij deze uitkomst zichtbaar in errors en alerts.

**Fwupd is niet uitgezonderd.** Health en de health-userunit blijven daarom
terecht exit 1/failed tonen zolang de systemunit gefaald staat. Dit is geen
geclaimde volledige groene host en geen geclaimde reparatie van de CDN.

### Gezond, defect en onbekend onderscheiden

De oude SSH-check keek alleen naar ssh.service en zou geldige socketactivatie
met een nog inactieve service foutief als SSH-uitval behandelen. Nu wordt ook
ssh.socket gecontroleerd. Actieve luistersocket met normaal inactieve service
is geldig; een failed-service/socket blijft fout. Geen wijzigingen aan SSH.
Dit corrigeert een reproduceerbare fout in een fixture; actuele SSH was al actief.

Een oude bootmelding `reboot-required` is een zichtbare onderhoudswaarschuwing,
geen automatische reboot of zelfstandige outage. Het ontbreken van optionele
bwrap/docker-tools blijft inventaris; geen runtime of nieuwe sandbox onderzocht.

Subprocesswaarnemingen hebben elk maximaal drie seconden; time-outs en ontbrekende
commando's worden vastgelegd als meetfout zonder exception-/stderrlek. RAM,
schijf en load worden onafhankelijk afgevangen zodat één kapotte meting niet
alle andere waarnemingen vóór latest.json blokkeert. De limieten RAM <2 GiB en
root vrij <15 GiB blijven exact behouden.

Latest/history krijgen dezelfde definitieve classificatie. Budgetwaarschuwing
blijft zichtbaar in stdout/latest; oude historie wordt niet gewist. Bij
schrijffouten volgen expliciete collector_errors. History openen weigert
symlinks, gebruikt 0600 vanaf creatie; latest blijft atomisch 0600. Budgetten
1 MiB/dag en 128 MiB totaal zijn niet verhoogd.

Er is geen nieuwe automatische remediatie, alarmlevering, tunnelprobe of
workerheartbeat toegevoegd. Die andere verbeterstappen blijven afzonderlijk.

## 3. Tests en live-acceptatie

**76 tests geslaagd**, waaronder twintig nieuwe tests in `tests/test_health.py`.
Alle ongezonde scenario's zijn fixtures/mocks of tijdelijke bestanden, geen
uitval van echte diensten of echte resourcebelasting.

Getest: gezonde host; fwupd-fout blijft exit1; onbekende failed-unit blijft fout;
collectorcommandofout/-time-out en ongeldige uitvoer; normale SSH-socketactivatie;
SSH beide uit, failed-service met actieve socket en onbekende toestand; lage
RAM/schijfruimte; NTP no versus meetfout; rebootwaarschuwing; ontbrekende optionele
tools; onleesbaar geheugen; gecombineerde bekende en onbekende fouten;
private/eenduidige latest/history; vol historiebudget; symlinkweigering;
onbeschrijfbare latest. Bestaande MVP/MCP/tunnel-/backuptests blijven slagen.

Reproduceerbaar:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_health.py -v
PYTHONDONTWRITEBYTECODE=1 ~/.local/share/server5-commandcenter/mcp-venv/bin/python -m unittest discover -s tests -q
PYTHONDONTWRITEBYTECODE=1 python3 scripts/commandcenter.py status
```

De laatste live status heeft collector_errors leeg, errors alleen
firmware_metadata_refresh_failed, warnings reboot_required, SSH-service en socket
actief en NTP yes. Verwachte exitcode is **1** wegens die echte fwupd-fout.
De reguliere timeruitvoering bevestigde hetzelfde, zonder herstart van de timer.
De stdout van status bevat nooit de metadata-HTTP-foutbody.

Regressie: MCP initialize/discovery en beide leestools geslaagd; start_task
niet aangeroepen. Tunnel live/ready en geauthenticeerde Platform-polling geslaagd.
Private HTTPS-webhealth ready/server5. Negen taken en 129 events hebben identieke
rij-digests aan de vooraf gemaakte backup; geen echte Codex-opdracht gestart.
Broker-PID 27844, adapter-PID 36942 en tunnel-PID 35324/restarttellers bleven gelijk.
Serve- en credential/config-bytes, overige oude bronbestanden en userunits bleven
ongewijzigd. Dit bewijst geen nieuwe echte Codex/modelaanroep; de idle worker is
behouden en de bestaande mock-worker-tests slagen.

## 4. Risico's en rollback

Nieuw schema en specifiekere alertcodes kunnen externe handmatige JSON-lezers
raken. Er zijn in de repository geen andere programmatische consumers van
latest/alerts gevonden; bestaande top-level resourcevelden en alerts blijven
bestaan. Nieuwe collector-exitcode 2 is bewust eveneens een mislukte meting,
geen SuccessExitStatus-truc. Een warning-only status krijgt exit0 maar blijft
met status=warning en alerts zichtbaar. Lokale output is geen externe alarmering.

Rollback: herstel alleen `scripts/commandcenter.py` uit
`~/.local/share/server5-commandcenter/step2-health/20261021-135818/commandcenter.py`,
of revert uitsluitend de eigen stap-2-commit. Dit behoudt de stap-1-backupfunctie.
De nieuwe health-helper/test/docs kunnen ongebruikt blijven staan. Volgende
reguliere meting gebruikt weer de oude logica; geen app-/tunnelherstart nodig.
Bewaar alle meetbestanden, diagnose en backups. Geen productie-DB terugzetten,
geen systemunit maskeren/resetten, geen netwerk-/SSH-/Tailscale-actie.

De echte metadatafout verdwijnt pas na een geslaagde normale fwupd-refresh;
verberg hem niet via een ignorelijst, SuccessExitStatus=1, timeruitschakeling,
certificaatcontrole uitzetten of een speculatieve netwerk-/IPv6-aanpassing.

## Definitieve aanvullende downloadmeting

De langere GET van uitsluitend `firmware.xml.zst.jcat` eindigde na 130 seconden
met curl exit28, HTTP000 en nul bytes. Er kwam dus ook binnen dat ruimere venster
geen signatureantwoord. De HTTP503 zelf is rechtstreeks door de metadata-refresh
van fwupdmgr gerapporteerd; de precieze URL bij die 503 werd niet meegegeven.
Daarom is niet geclaimd dat de 503 bewezen van precies de signature-URL kwam.
Alle curl-proeven behielden TLS-verificatie en sloegen responsebodies niet op.
