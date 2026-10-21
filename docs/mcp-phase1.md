# Fase 1 — lokale MCP-adapter, 2026-10-21

Uitgevoerd volgens de expliciete fase-1-opdracht van de eigenaar. Alleen server5
gewijzigd. De eigenaar is de enige toegestane gebruiker. Geen tunnel-client,
API-key, OpenAI-tunnelwijziging of echte Codex-proef uitgevoerd.

## Implementatie

- `web/mcp_adapter.py`: officiële Python MCP-SDK 1.30.0, stateless Streamable
  HTTP met JSON-antwoorden op `http://127.0.0.1:8796/mcp`.
- Alleen `task_status(task_id)` en `task_result(task_id, offset=0, limit=4096)`.
  Beide tools hebben readOnlyHint en idempotentHint. Geen start-, cancel-,
  shell-, lijst- of bestandsgereedschap. `start_task` is niet geregistreerd.
- De adapter hergebruikt `Store.get`, `TERMINAL` en `redact` uit de bestaande
  broker. Een ReadOnlyStore slaat de muterende constructor over en opent de
  bestaande database met SQLite mode=ro en query_only. Geen schema-initialisatie,
  recover(), claim(), worker of brokerlock in de adapter.
- Status geeft uitsluitend metadata terug, geen opdrachttekst. Resultaatpagina's
  bevatten maximaal 4096 tekens, met next_offset; totale tekst maximaal 64000
  tekens. Redactie gebeurt vóór paginering, met aanvullende afscherming van het
  eigen credential. Geen events/raw logs of websessies worden aangeboden.
- Iedere HTTP-route vereist `Authorization: Bearer ...`, ook initialisatie en
  discovery. Vergelijking in constante tijd. Geen browser-Origin toegestaan;
  Host is beperkt tot 127.0.0.1:8796. Geen CORS of proxy-headervertrouwen.
- Verzoeken maximaal 16 KiB, maximaal 16 gelijktijdige verbindingen. Geen
  accesslogs; logfilter schermt het eigen credential en bekende secretpatronen af.
- Aparte userunit `systemd/user/server5-mcp.service`, enabled/active als mau,
  maximaal 256 MiB, 50% CPU en 32 taken. NoNewPrivileges, read-only home/system
  en private tmp. Alleen deze nieuwe dienst is tijdens acceptatie herstart.

## Credential en afhankelijkheden

Credential: `~/.config/server5-commandcenter/mcp-token`, uitsluitend lokaal,
mode 0600, willekeurig gegenereerd zonder terminaloutput. De directory is privé.
De loader weigert symlinks, te ruime bestandsrechten en verkeerde eigenaar.
Het credential wordt bij start gelezen; vervangen vereist adapterherstart.
Geen webwachtwoord of Codex-authbestand gekopieerd.

Deze bearer verleent leestoegang als eigenaar; het is geen OAuth-gebruikerslogin.
Processen onder dezelfde Linux-gebruiker kunnen het credential lezen. Deel dit
credential niet met andere workspacegebruikers. Redactie is aanvullend en geen
garantie dat willekeurige gevoelige taakinhoud automatisch wordt herkend.

Geïsoleerde Python-omgeving:
`~/.local/share/server5-commandcenter/mcp-venv`.
Alle geïnstalleerde versies staan in `requirements-mcp.lock`.
Systeem-Python en de bestaande webservice zijn niet aangepast. ensurepip/pip
ontbraken; installatie gebeurde zonder sudo met een venv en de officiële
PyPA pip.pyz-bootstrap. `pip check` meldt geen gebroken afhankelijkheden.

Herinstallatie, alleen wanneer nodig, met een nieuwe lege omgeving:

```bash
python3 -m venv --without-pip /home/mau/.local/share/server5-commandcenter/mcp-venv
curl -fsS https://bootstrap.pypa.io/pip/pip.pyz -o /tmp/server5-mcp-pip.pyz
/home/mau/.local/share/server5-commandcenter/mcp-venv/bin/python /tmp/server5-mcp-pip.pyz install -r requirements-mcp.lock
```

Maak bij herstel een nieuw credential aan zonder het te tonen, bijvoorbeeld met
Python secrets.token_urlsafe(48), umask 077 en exclusief aanmaken van het bestand.
Neem nooit de waarde op in een commandoargument, unit, Git, Notion of rapport.
Kopieer vervolgens uitsluitend de nieuwe unit naar `~/.config/systemd/user/`,
voer daemon-reload uit en enable --now server5-mcp.service. Dit herstart de
bestaande webservice niet. De secrets en venv worden bewust niet in Git bewaard.

## Bewijs en tests

Alle 19 tests geslaagd: 8 nieuwe MCP-tests en 11 bestaande broker/HTTP/hersteltests.
De bestaande workertests gebruiken uitsluitend mock-Pythonprocessen. Er is geen
echte Codex-worker gestart.

```bash
/home/mau/.local/share/server5-commandcenter/mcp-venv/bin/python -m unittest discover -s tests -v
/home/mau/.local/share/server5-commandcenter/mcp-venv/bin/python scripts/check-mcp.py
systemd-analyze --user verify systemd/user/server5-mcp.service
git diff --check
```

Gebruik de venv-Python: systeem-Python slaat MCP-tests over omdat de SDK daar
bewust niet geïnstalleerd is. De SDK/TestClient meldt een deprecatiewaarschuwing
over httpx; de tests slagen. Geen wijziging aan dependencies alleen voor die waarschuwing.

Gedekt: initialize, tools/list, geldige status/resultaat, weigering start_task,
ontbrekende/verkeerde authenticatie bij GET/POST/DELETE, verkeerde Host/Origin,
ongeldige en onbekende IDs, parametergrenzen, redactie vóór paginering,
resultaatbegrenzing, te grote verzoeken, credentialrechten/symlinks en
read-only SQL. Herinitialisatie laat een running-taak ongemoeid.

De officiële SDK-client heeft tegen de actieve lokale dienst geïnitialiseerd,
beide tools ontdekt en een bestaande productietaak gelezen. Dezelfde smoke
slaagt na een echte systemd-herstart van alleen server5-mcp.service. Geen
opdracht ingediend. Nieuwe PID adapter 34196; bestaande broker bleef PID 27844.
Automatisch herstarten na procesfout is geconfigureerd; reboot niet getest.

## Backup en regressie

Voor de eerste projectwijziging zijn bronbestanden, baseline/hashes en een
consistente taakdatabasekopie gemaakt onder:
`~/.local/share/server5-commandcenter/phase1-backups/20261021-115753/`.
SQLite integrity_check=ok; login-sessies uit de backup verwijderd. Dit is een
lokale herstelkopie op dezelfde SSD, geen externe rampenbackup.

Alle bestaande projectbestanden zijn na implementatie bytegelijk aan de baseline;
bestaande ongecommitte wijzigingen behouden. Taken en events gelijk aan de
databasebackup; Serve-configuratie ongewijzigd.

- Webservice active, PID 27844, geen herstart. HTTP/private HTTPS-health ready.
- Beide apppoorten uitsluitend 127.0.0.1:8795 en 127.0.0.1:8796.
- Serve blijft uitsluitend naar 8795 verwijzen; geen Funnel of publieke route.
- Alle drie timers active. Taakbackup handmatig gestart: Result=success,
  integrity_check=ok en nul login-sessies in de nieuwe kopie.
- Monitoring werkt maar meldt een bestaande hostfout: fwupd-refresh.service,
  aantoonbaar aanwezig om 11:35 UTC vóór implementatie. Daardoor eindigt
  server5-health.service met exitcode 1. Niet gereset of gerepareerd in deze fase.
- Laatste configuratiebackup Result=success. Deze bestaande backup accepteert
  alleen een schone Git-boom; de reeds aanwezige ongecommitte wijzigingen blijven
  een beperking voor de volgende automatische configuratiebackup. Daarom is voor
  deze fase een afzonderlijke bronbackup gemaakt. Geen bestaande backupregel
  aangepast en geen brede commit van andermans wijzigingen uitgevoerd.

## Later verbinden met de tunnel-client — nog niet uitvoeren

Doeladres wordt http://127.0.0.1:8796/mcp. De huidige bearer is uitsluitend een
lokaal credential, geen OpenAI API-key. De tunnel-client krijgt later een
afzonderlijke restricted Platform-runtimekey en het bestaande tunnel-ID.

De huidige clientdocumentatie ondersteunt `mcp.extra_headers` met file:-referenties.
Voor Authorization moet het referentiebestand de volledige headerwaarde bevatten,
dus Bearer gevolgd door het lokale token. Laat die waarde later in een apart
0600-bestand buiten Git afleiden, zonder uitvoer. Bijvoorbeeld profielvorm:

```yaml
mcp:
  extra_headers:
    Authorization: file:/home/mau/.config/server5-commandcenter/mcp-authorization-header
```

Dit headerbestand is nu NIET aangemaakt. Het doeladres en control-planecredential
moeten later samen volgens de dan geïnstalleerde clientversie worden ingesteld.
Doorgestuurde Authorization-headers kunnen de statische header overschrijven;
dit expliciet testen. Controleer ook Host/Origin-gedrag zonder nu de lokale
toegangsregels te verruimen. Tunnelrechten beperken tot de eigenaar; deze lokale
adapter bewijst zelf geen ChatGPT-gebruikersidentiteit. Geen OAuth of publieke
metadata toegevoegd. Mobiele tekst, tunnel en Live-spraak blijven onbewezen.

Bronnen:
- https://developers.openai.com/plugins/build/mcp-server
- https://github.com/openai/tunnel-client/blob/main/docs/configuration.md
- Notion-plan: https://app.notion.com/p/400c7b0333768136ba9be0a112f10b45

## Rollback

```bash
systemctl --user disable --now server5-mcp.service
```

Hiermee stopt uitsluitend de nieuwe listener. Laat database, webapp, Tailscale,
Codex-login, bestaande diensten en backups intact. Verwijder bij definitieve
uitfasering alleen de nieuwe unit, adapterbestanden en geïsoleerde venv na review;
daarna daemon-reload. Trek het lokale credential in door het veilig te vervangen
of de uitgeschakelde dienst zonder geldig credential te laten. Geen SQLite-
restore nodig: de adapter heeft geen taakdata gewijzigd. Bij bronherstel eerst
het beschermde projectarchief elders uitpakken en vergelijken, nooit blind over
de bestaande ongecommitte wijzigingen heen herstellen.

## Resterend

Geen handmatige stap nodig voor de lokale fase. Voor vervolg: tunnel-client en
runtimekey afzonderlijk vrijgeven, eigenaarstoegang en transportheaders testen,
vervolgens ChatGPT web/telefoon en pas daarna Live-spraak. start_task blijft uit.

Notion-uitvoeringsverslag (teruggelezen):
https://app.notion.com/p/400c7b033376817d929ae2db42d560dc
Het gedeelde werklog en oorspronkelijke onderzoeksplan verwijzen naar dit verslag.
