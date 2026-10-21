# Implementatieplan — 2026-10-21

## Besluit en prioriteiten
Server5 (OptiPlex 5070, Ubuntu 24.04.5, i7-8700, 7.5 GiB RAM) wordt eerst een kleine beheerhost. Git is bron, Notion een gecontroleerde momentopname, MindMap AI de architectuurweergave. Geen zware AI-modelserver, databasecluster, Kubernetes of publieke dienst in deze tranche. Bestaande LAN-SSH blijft het herstelpad.

1. P0 / fase 1: inventaris herbevestigen, bestaand protocol lezen, plan en Git-baseline vastleggen. Geen afhankelijkheden; risico beperkt tot nieuwe lokale bestanden. Rollback via Git-revert; oudere rapporten behouden als historische feiten.
2. P0 / fase 2: sudo, SSH, AppArmor en bwrap controleren; distributiepakket installeren met eenmalige gebruikersauthenticatie. Afhankelijk: rootautorisatie in de eigen terminal. Geen sudoers-wijzigingen. Risico: pakket- en AppArmor-profielwijziging; simulatie en specifieke profielcontrole vooraf, geen globale beveiligingsverlaging. Rollback: beoordeelde profielwijziging terugzetten; geen automatische pakketverwijdering of reboot.
3. P1 / fase 3: Tailscale installeren en aansluiten na roottoegang en tailnetkeuze. Geen DNS-acceptatie, subnetroutes, exit-node, Funnel of Tailscale SSH. Een extra client moet gewone SSH via het tailnet testen. Bij mogelijke LAN/SSH-impact afzonderlijke bevestiging en consoleherstel nodig. Rollback: tailscale down via bestaande LAN-SSH; installatie behouden voor diagnose.
4. P1 / fase 4: rootless containeromgeving pas na werkende namespaces en gecontroleerde pakketvoorbereiding. Voorkeur rootless Docker met Compose indien distributie-/AppArmor-voorwaarden passend zijn; geen rootful daemon of docker-groepsrechten toevoegen. Eerste workload alleen na aantoonbare behoefte; CPU maximaal 1, RAM 256 MiB, PIDs 64, read-only root, cap_drop ALL, no-new-privileges, persistentie expliciet, geen gepubliceerde poorten. Rollback: uitsluitend nieuwe testworkload stoppen, volumes behouden. Runtime nog niet aanwezig.
5. P1 / fase 5: nu uitvoerbaar zonder root: versiebeheer, kleine Python-hostmeting, systemd-usertimer, begrensde lokale historie, allowlist-configbackup, geïsoleerde herstelprocedure. Backups op dezelfde SSD zijn alleen lokale herstelkopieën, geen disaster recovery. Externe backupbestemming vereist latere keuze, geen server3 benaderen.
6. P1 / fase 6: veilige werkstroom opdrachten → Codex → lokaal bewijs/Git → Notion/MindMap. Bestaande sessieconnectoren gebruiken; geen API-secrets of shell-endpoint introduceren. Geen claim van permanente ChatGPT-shelltoegang. Geen onbeheerde uitvoering van tekst uit Notion.
7. P1 / fase 7: scripts en systemd-units controleren, timers uitvoeren, allowlist-backup herstellen in tijdelijke map, hashes vergelijken, poorten/routes voor/na controleren. Geen reboot. Herstartbestendigheid van userdiensten blijft afhankelijk van linger of gebruikerslogin; volledige acceptatie wacht op toegangs- en containertests.

## Capaciteit en herstelcriteria
Hostbeheer heeft voorrang op experimenten. Reserveer ten minste 2 GiB beschikbaar RAM en 15 GiB vrije rootruimte. Geen disklayout wijzigen. Monitoring elke 5 minuten, backup dagelijks, geen cloudkosten. Oude lokale kopieën niet automatisch wissen in deze tranche.

## Validatie fase 1
Hardware/OS opnieuw via hostnamectl; ip toont 192.168.1.245/24 eno1 en ongewijzigde default gateway. systemctl --failed: nul. SSH actief, poort 22 op IPv4/IPv6. sudo -n true faalt met password required. Usermanager werkt; Linger=no. Volledige sshd-configcontrole zonder root geweigerd door cloud-init-configrechten. Geen beveiligingsbeperkingen omzeild.

## Wijziging, risico en rollback
2026-10-21: dit plan en faseverslag toegevoegd om afhankelijkheden en stopgrenzen expliciet te maken. Git-identiteit repository-lokaal als technische agent ingesteld; geen persoonlijke identiteit aangenomen. Alleen lokale niet-gevoelige bestanden opgenomen. Herstel door gerichte Git-revert; runtime ongewijzigd.
