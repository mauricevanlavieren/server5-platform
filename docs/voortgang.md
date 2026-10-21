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
