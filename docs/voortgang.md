# Voortgang — 2026-10-21 UTC

## Fase 1 — afgerond
Wijziging: actuele inventaris bevestigd, protocol gelezen, implementatieplan en Git-baseline opgesteld.
Reden: reproduceerbare, lichte basis met expliciete afhankelijkheden.
Validatie: hostname server5, OptiPlex 5070, Ubuntu 24.04.5, SSH en AppArmor actief; nul gefaalde systeemunits; LAN 192.168.1.245.
Risico: alleen lokale documentatie en repo-instellingen. Rollback: gerichte Git-revert, geen netwerkimpact.
Volgende actie: bwrap/SSH-rootcontrole voorbereiden; root vereist gebruikershandeling. Onafhankelijke monitoring/backup blijft uitvoerbaar.

## Mindmap-updates voor ChatGPT
De MindMap AI-connector kan deze kaart lezen. Schrijftoegang wordt met de geautoriseerde feitencorrecties getest. Pas hardware aan naar OptiPlex 5070; OS naar 24.04.5; Node/Codex aanwezig; Docker/Tailscale ontbreken. Werk autonomiegrens bij naar uitsluitend server5 en afzonderlijke bevestiging voor beschikbaarheidsimpact. Verdere voorstellen in oude kaart zijn niet automatisch goedgekeurd.

## Fase 2 — controles uitgevoerd; herstel wacht op gebruiker
2026-10-21. Wijziging: scripts/prepare-security.sh toegevoegd, bash -n geslaagd. Reden: sudo-authenticatie moet in de eigen terminal plaatsvinden; geen sudoers-verruiming of credentials in chat.
Validatie: SSH actief; .ssh 700/authorized_keys 600; sshd -t zonder root geweigerd door bestaande bestandsrechten. AppArmor actief; bwrap ontbreekt. Eerdere helpertest faalde op UID-map. sudo -n true vereist wachtwoord. Geen configuratie gewijzigd. Sysstat sar21 bevat CPU-metingen tot 05:30 UTC: historie werkt ondanks ENABLED=false in legacy-config; niet wijzigen.
Risico: alleen aangeboden pakketinstallatie kan systeemwijziging veroorzaken; script toont simulatie, verbiedt verwijderingen en herstart SSH niet. Rollback: geen huidige runtimewijziging. Bij bwrap-profielproblemen eerst diagnose/specifiek profiel; globale AppArmor-instellingen behouden.
Gebruikershandeling aangevraagd: bash scripts/prepare-security.sh in eigen terminal. Fase is niet volledig afgerond tot package/sandbox/sshd-rootvalidatie slagen. tldraw blijft ongeautoriseerd.

## Fase 3 — voorbereidingsdeel afgerond; aansluiting wacht
2026-10-21. Procedure in docs/toegang-en-containers.md. Tailscale ontbreekt; geen installatie of login. Afhankelijk van sudo en door gebruiker gekozen tailnet. Validatie beperkt tot lokale prerequisites, dus veilige VPN-toegang nog niet bewezen. Risico en rollback vooraf beschreven. Volgende actie: lokaal beheer onafhankelijk verder uitvoeren.

## Fase 4 — ontwerp afgerond; runtime nog niet geïnstalleerd
2026-10-21. Rootless Docker als voorkeur; geen rootful Docker, Kubernetes of onnodige workload gestart. Subuid/subgid-range aanwezig, uidmap-tools ontbreken; usernamespace-/AppArmorcontrole en sudo vormen afhankelijkheden. Resource-/persistentie-/rollbackcriteria in docs/toegang-en-containers.md. Validatie runtime uitgesteld, geen succesvolle containertest geclaimd. Volgende actie: fase 5 monitoring en lokale configuratiebackups zonder root inrichten.

## Fase 5 — lokale beheerbasis actief; externe backup open
2026-10-21. Wijziging: Python-hostmeting, begrensde historie, dagelijkse configuratiebackup, usertimers en credential-commitguard geïmplementeerd. Host-AGENTS gekopieerd naar Git voor herstel. Reden: lichte controleerbare automatisering zonder poorten of rootverruiming.
Validatie: vier herstelveiligheidstests geslaagd (traversal, links/devices, reguliere bestanden, corrupte checksum); systemd-unitcontrole geslaagd; beide handmatig gestarte units Result=success/ExecMainStatus=0; timers enabled en gepland. Werkelijk archief van commit 86ef6be hersteld in tijdelijke map: 19 bestanden byte- en executable-bitgelijk, geen productiegegevens geraakt. Gegenereerde pyc-bestanden zijn uit Git-index gehaald en genegeerd, lokale bestanden behouden.
Risico: alleen usertaken, begrensd CPU/RAM/diskgebruik; secretsguard is heuristiek. Backups beschermen alleen gecommitte configuratie op dezelfde SSD. Linger=no beperkt automatisering na boot. Geen remote, externe backup of externe alerts ingericht.
Rollback: timers disable --now; meet-/backupbestanden bewaren; gerichte Git-revert. Zie docs/beheer-en-herstel.md. Volgende actie: samenwerkingsworkflow met expliciete overdrachten en bewezen connectoren vastleggen.

## Fase 6 — veilige sessieworkflow geïmplementeerd
2026-10-21. Wijziging: docs/samenwerking.md, overdrachtsjabloon en Git-Markdown-export met SHA256; AGENTS aangevuld met geautoriseerde fasepublicaties en bestaande grenzen. Reden: consistente overdracht zonder nieuwe shellservice of credentials. Validatie: sessie voert lokaal uit en schrijft aantoonbaar via Notion/MindMap; exportcontrole op schone Git-boom. Geen permanente online ChatGPT-shellintegratie of onbeheerde externe synchronisatie geclaimd. Risico: nieuwe bestanden en expliciete publicaties; rollback met gerichte Git-revert. Volgende actie: end-to-end lokale herstel-/timer-/netwerkcontrole en open afhankelijkheden rapporteren.
