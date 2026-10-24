# Server5 herstelpakket — RCCAP

Taak: server5_recovery_package_20261024_001. Kaartstatus Blocked; de echte
brokerstatus blijft running tot workerexit en wordt niet via de database gewijzigd.

Oorzaak: applicatierepository /home/mau/server5-commandcenter heeft geen remote
(git remote -v en remote-config leeg); geen andere applicatierepo gevonden onder
/home/mau (alleen .nvm is een dependencyrepo). Geen gh-client beschikbaar.
Geen gepubliceerde GitHub-bron of bestaande doelrepository kon worden vastgesteld.
Geen externe systemen gewijzigd en geen push uitgevoerd of bewezen.

Oplossing/volgende actie: eigenaar beantwoordt beslis-ID
server5_recovery_remote_20261024_001 met bestaande owner/repo of credentialvrije URL.
Daarna bestaande remote instellen, authenticatie via bestaande login laten werken,
pushen en eenmaal remote-tip tegen lokale commit controleren. Geen nieuwe repo maken.
Het 60-secondenwachten eindigde zonder antwoord; timeout is geen toestemming.

## Lokaal resultaat en inventaris

RESTORE.md beschrijft de exacte volgorde en expliciete voorwaarden/beperkingen.
Bestaande broncode nu geselecteerd voor lokale commit: broker/webchat, Codex-worker,
MCP reads/decisions/cancel, Current Projects lifecycle, statische mindmapviewer,
Node lockfile, Python lockfile, tien bestaande user units en instructies.
Exacte gewijzigde commitbestanden: files.txt (in dezelfde map).
Al reeds tracked bron blijft via Git beschikbaar. Historische plannen, taakbackups,
private config, inventarisdata, losse .bak/.backup bestanden, node_modules en
mindmapgeschiedenis zijn niet toegevoegd. Geen nieuwe software/scripts/services gemaakt.
De tien systemd/user-units zijn bytegelijk aan de geïnstalleerde user units.
Node v22.23.3, Codex CLI 0.163.0; MCP-venv bestaat onder ~/.local/share/server5-commandcenter.
Tunnel-client is bestaande lokale binary ~/.local/bin/tunnel-client; tunnel-unit
verwijst naar private configuratie, waarvan geen inhoud is geopend.
Geen lokale Codex auth/config of andere credentials geopend/gekopieerd.

Niet herstelbaar vanuit Git alleen: SQLite tasks/decisions, logs, mindmaptoestand,
imports/historie/bewijs/bindings, lokale backups, credentials en accounts,
SSH/Tailscale-identiteiten en privé-Serve-config, tunnelregistratie/key en binary,
Codex skills/persoonlijke config en optionele Ollama-modellen. Externe dependency-
registries blijven nodig; dit is geen offline/imagebackup. Zonder aparte data-
backup kan alleen een lege omgeving worden ingericht. Geen herstel op vervanger getest.

## Validatie

Staged credential guard geslaagd (heuristisch; geen garantie voor alle history).
Alle geselecteerde Python-bronnen syntactisch geparseerd.
7 MVP-tests en 5 decisions-tests geslaagd, met tijdelijke testtoestand/mockworkers.
Bestaande test_mcp_mindmap: 5 tests, 1 failure en 2 errors; fixture schrijft de
oude map.json/import-Markdown, terwijl productievalidator current-projects.json
leest. Geen productcode aangepast om deze oude tests te laten slagen.
Live validator met bestaande MCP-venv geslaagd voor publicatie met 5 nodes;
standaard /usr/bin/python3 mist pydantic, daarom bestaande venv gebruikt.
Eindbewijs in ../current-projects/server5_recovery_package_20261024_001-final-validation.json.
Nodes vóór→piek→na: 1→5→3. Eigen inventaris- en pakketstappen zijn met bewijs
weggesnoeid; push/remoteverificatie blijft rood open. Geen groen eindresultaat.

## Rollback

Geen service/netwerk-/runtimeconfig gewijzigd. Herstelcommit gericht reverten als
het lokale pakket ongewenst is, met behoud van vooraf bestaande werkboomwijzigingen.
Mindmap vóór- en tussentoestand staan onder docs/mindmaps/current-projects/;
alleen onder exclusieve writer.lock terugzetten als deze taak nog eigenaar is en
broker niet meer schrijft. Oude task_id/status nooit als nieuwe brokerstatus uitgeven.
Geen reset --hard, clean, herstart of verwijdering uitgevoerd.
