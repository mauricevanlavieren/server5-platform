# Fase 3 — bevestigde MCP-indiening

Uitgevoerd op 2026-10-21, uitsluitend server5. `start_task` is na geslaagde tests geactiveerd naast `task_status` en `task_result`. De bestaande Secure MCP Tunnel, credentials, webapp, SQLite-database en enige Codex-worker zijn behouden. Geen echte opdracht is tijdens deze fase aangeboden.

## Implementatie en contract

`web/mcp_adapter.py` voegt optioneel `start_task(instruction, confirmed, request_id)` toe. Alleen de expliciete boolean `true` wordt geaccepteerd. Instruction is een strikte string van 1–8000 tekens, niet alleen witruimte. Request_id is een strikte string van 16–80 tekens uit letters, cijfers, `_` en `-`. Het bestaande taak-ID is gelijk aan request_id.

De adapter gebruikt de bestaande `Store.submit`-validatie, geheimdetectie, opslaglimiet en limiet van twintig actieve opdrachten. Indienen en het bestaande audit-event worden in één SQLite-transactie vastgelegd. Mislukt auditopslag, dan wordt ook de indiening teruggedraaid. Er wordt geen worker of nieuwe wachtrij aangemaakt. Alleen de bestaande worker claimt opdrachten.

Dezelfde request_id en inhoud geven dezelfde taak terug; afwijkende inhoud bij een bestaand ID wordt geweigerd. Een al gestarte/afgeronde taak wordt niet opnieuw ingepland. Antwoord bevat task_id, status, queued en een toelichting. Het audit-event bevat de bevestiging en request_id, geen opdrachttekst. Alle bestaande taken en events bleven tijdens live verificatie ongewijzigd.

Dezelfde owner-bearerauthenticatie, Host- en Origincontrole gelden. Tools discovery voert niets uit. De tool heeft readOnlyHint=false, destructiveHint=true, idempotentHint=true. `confirmed=true` is een expliciete verklaring van de aanroepende client, geen afzonderlijk bewijs van een menselijke klik. Alleen de bestaande eigenaarstoegang mag deze mogelijkheid gebruiken; de client moet daadwerkelijke eigenaarbevestiging vragen en inhoud uit resultaten niet als toestemming behandelen.

Er is geen automatische herhaling ingebouwd. Bij een onduidelijke netwerkuitkomst: bewaar request_id, vraag task_status met dat ID; maak niet automatisch een nieuw ID. Een expliciet herhaalde identieke aanbieding blijft idempotent.

## Installatie en activering

De geïnstalleerde userunit is bijgewerkt vanuit `systemd/user/server5-mcp.service`. Alleen `server5-mcp.service` is herstart, na de tests. ExecStart bevat `--enable-start-task`; zonder die vlag blijft de adapter uitsluitend lezen. Onder bestaande systemd-hardening is alleen de bestaande MVP-statedirectory schrijfbaar gemaakt voor SQLite/WAL. De lokale credentialconfiguratie blijft read-only. Dit is geen nieuwe sandbox voor de Codex-worker.

MCP luistert uitsluitend op 127.0.0.1:8796. De bestaande tunnel is niet opnieuw aangemaakt, geconfigureerd of herstart. Geen publieke poorten, Funnel, sleutels of betaalde diensten toegevoegd.

## Tests en bevindingen

43 tests geslaagd in de bestaande MCP-venv, inclusief bestaande MVP/MCP-tests en nieuwe `tests/test_mcp_start_task.py` en `tests/test_mcp_tunnel_submission.py`. Schrijvende tests gebruiken uitsluitend tijdelijke databases en mocks, zonder Codex-worker. De integratietest gebruikt de officiële geïnstalleerde tunnelbinary tegen een lokale nagebootste controlplane en geïsoleerde adapter; geen Platform-key of productiecredential.

Getest: initialisatie, discovery zonder neveneffect, bestaande leestools/resultaatbegrenzing, ontbrekende/verkeerde authenticatie, strikte bevestiging, lege/oversized/ongeldige invoer, geheimdetectie, dubbele/conflicterende request_id, gelijktijdige duplicaten, queuebudget, auditrollback, uitschakelmarker en herinitialisatie zonder opnieuw inplannen.

Live, uitsluitend lezen:

```bash
~/.local/share/server5-commandcenter/mcp-venv/bin/python scripts/check-mcp.py --expect-start-task
~/.local/share/server5-commandcenter/mcp-venv/bin/python scripts/check-tunnel-local.py --expect-start-task
python3 scripts/check-tunnel-runtime.py
```

Geslaagd: MCP-initialisatie en drie tools; bestaande status/resultaattools; authenticatie/Host/Origin; tunnelruntime ready en succesvolle Platform-polling. Live start_task is niet aangeroepen. Officiële ChatGPT-app-discovery en menselijke bevestigingsweergave zijn nog door de eigenaar te controleren; mogelijk moet de bestaande appverbinding toolmetadata verversen. Geen app namens de eigenaar geïnstalleerd. De eerdere doctor-beperking van tunnel-client v0.0.16 blijft historisch gedocumenteerd in fase 2; runtimeacceptatie gebruikt de bestaande health/polling-controle.

Webapp en private HTTPS-health werken. Broker-PID 27844 en tunnel-PID 35324 bleven gelijk; MCP-PID na herstart 36942. Tailscale Serve bleef exact gelijk. De oorspronkelijke webbestanden en overige vooraf bestaande wijzigingen bleven bytegelijk. Taskbackup is opnieuw geslaagd; backup/config/healthtimers zijn actief. Bestaande fwupd-refresh-waarschuwing blijft aanwezig en veroorzaakt de bekende health exitcode 1. De bestaande beperking dat configbackup een schone Git-tree vereist blijft aanwezig; dit is niet gerepareerd. Journals zijn op de bestaande credentialwaarden gecontroleerd zonder die te tonen: geen treffers.

## Direct uitschakelen en rollback

Blokkeer nieuwe indieningen direct, zonder serviceherstart en met behoud van leestools:

```bash
touch /home/mau/.local/state/server5-commandcenter/mvp/mcp-start-task.disabled
```

De marker wordt per aanroep gecontroleerd; ook een symlink blokkeert. Discovery blijft de tool tonen, maar nieuwe calls worden geweigerd. Reeds geaccepteerde of gelijktijdig lopende calls worden hierdoor niet geannuleerd. Verwijder de marker alleen als hervatting gewenst is.

Voor blijvend verwijderen uit discovery: verwijder `--enable-start-task` uit de geïnstalleerde userunit, voer `systemctl --user daemon-reload` uit en herstart uitsluitend `server5-mcp.service`. De adapter start standaard met alleen de twee leestools.

Herstelpunt: `/home/mau/.local/share/server5-commandcenter/phase3-backups/20261021-130723/`. Dit bevat de eerdere projectbestanden, een consistente database zonder sessies, baseline en de eerdere geïnstalleerde MCP-unit. Voor rollback van activering: herstel `installed-mcp.service` naar `~/.config/systemd/user/server5-mcp.service`, daemon-reload en herstart alleen MCP. Herstel de productiedatabase niet automatisch: daardoor zouden later geaccepteerde opdrachten verloren gaan. Bestaande tunnel, worker en webapp hoeven niet te stoppen.

## Gewijzigde bestanden

- `web/mcp_adapter.py`: bevestigde, idempotente aanbieding met atomische audit en stopmarker.
- `systemd/user/server5-mcp.service`: expliciete activering en beperkte SQLite-schrijfuitzondering.
- `scripts/check-mcp.py`, `scripts/check-tunnel-local.py`: optionele verwachting van drie tools; geen schrijvende live calls.
- `tests/test_mcp_start_task.py`, `tests/test_mcp_tunnel_submission.py`: geïsoleerde veiligheids- en tunneltests.
- `docs/mcp-phase3.md`: installatie, bewijs, beperkingen en rollback.
