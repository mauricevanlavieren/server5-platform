# Beheer en herstel — 2026-10-21

## Fase 5: lokale implementatie
Wijziging: scripts/commandcenter.py biedt status, backup en restore-test. Vier systemd-userunits meten elke vijf minuten en maken dagelijks een herstelkopie van schone Git HEAD. Reden: beheerbaar zonder nieuwe poorten, zware stack of sudo. scripts/check-staged.py en .githooks/pre-commit blokkeren veelvoorkomende credentialbestanden/letterlijke sleutels vóór commits. Dit is een heuristiek naast handmatige review, geen volledige secretscanner. core.hooksPath is repository-lokaal; bij nieuwe clone opnieuw instellen.

## Metingen en logs
Statusbestand: ~/.local/state/server5-commandcenter/latest.json; dagelijkse health-YYYY-MM-DD.jsonl, maximaal 1 MiB per dag en 128 MiB totaal. Bij limiet stopt historieappend, latest toont history_budget_reached; geen historie automatisch gewist. Bestanden mode 600, mappen 700. Beschikbare RAM <2 GiB, rootruimte <15 GiB, gefaalde units, inactieve SSH en onbekende/onjuiste NTP veroorzaken exit 1 en een mislukte health-unit. reboot_required en ontbrekende tools staan als aparte aandachtspunten in JSON. De health-unit zelf kan na een alarm als failed in de volgende meting terugkomen; onderzoek de oorzaak en gebruik daarna systemctl --user reset-failed server5-health.service.

`python3 scripts/commandcenter.py status`
`systemctl --user status server5-health.timer server5-backup.timer`
`journalctl --user -u server5-health.service -u server5-backup.service --since today`

Er is geen externe alertlevering en geen actief 24/7 toezicht door ChatGPT. Journald bewaart taakuitvoer volgens bestaande hostretentie; die systeemretentie is niet gewijzigd. Sar-CPU-historie werkt reeds. Nieuwe unitbudgetten: health 96 MiB/10% CPU, backup 128 MiB/20% CPU; beide maximaal 16 taken en een timeout.

## Backupscope en beperkingen
Backup: ~/.local/share/server5-commandcenter/backups/<volledige-commit>.tar.gz plus checksum. Alleen een schone, gecommitte Git-boom; geen auth.json, .ssh, .codex, OS-config, .git-geschiedenis of workloadvolumes. docs/host-AGENTS.md is een versiebeheerbare kopie van /home/mau/AGENTS.md; handmatig gelijk houden bij instructiewijziging. Geen bestaande bronbestanden overschrijven tijdens backup. Eén archief per commit; maximaal 256 MiB nieuwe archieven, daarna foutmelding zonder verwijdering. Geen automatische pruning. Ongecommitte werk wordt bewust niet geback-upt; timerfaalstatus vraagt actie.

Deze kopieën staan op dezelfde SSD en beschermen niet tegen schijfverlies of volledige hostcompromittering. Externe offline/versleutelde backupbestemming moet nog door eigenaar gekozen worden; andere servers worden niet benaderd. Git-remote en credentials zijn niet ingesteld. RPO voor gecommitte configuratie: maximaal circa één dag zolang usermanager actief is; RTO nog niet voor volledige host gemeten.

## Herstelprocedure zonder productieschade
1. Controleer ruimte, eigenaar, oorzaak en gewenste Git-commit.
2. Start `python3 scripts/commandcenter.py restore-test /volledig/pad/<commit>.tar.gz` op server5. Dit controleert SHA256, weigert absolute/traversal-/link-/deviceleden, pakt uitsluitend uit in een tijdelijke map en vergelijkt alle bytes en executable bits met Git-objecten. Alleen de eigen tijdelijke testmap wordt na afloop opgeruimd.
3. Voor werkelijk herstel: pak een beoordeeld archief uit in een NIEUWE directory, vergelijk configuratie, en zet geselecteerde bestanden pas na beoordeling terug. Geen ongeteste tar-extractie over /home of /etc. Het testcommando heeft de bijbehorende lokale Git-objecten nodig; een later volledig hostherstel uit alleen het archief vereist handmatige broninspectie/checksum en nieuwe Git-initialisatie.
4. Herinstalleer benodigde distributiepakketten via vastgesteld plan; plaats beoordeelde userunits in ~/.config/systemd/user, daemon-reload en enable timers. Geen netwerk- of SSH-config vervangen.
5. Verifieer metrics, logs, route/poorten en applicatiedata apart. Authenticeer externe accounts opnieuw via officiële flow.

## Boot en rollback
Usertimers zijn persistent geconfigureerd waar relevant, maar Linger=no: zonder gebruikerslogin start de usermanager niet gegarandeerd. Ononderbroken monitoring na boot is dus nog niet bewezen. Linger activeren zou een expliciete rootgebruikershandeling zijn; nu niet uitgevoerd. Geen reboot gedaan.
Rollback: `systemctl --user disable --now server5-health.timer server5-backup.timer`. Bewaar gegenereerde meet-/backupbestanden; geen data verwijderen. Nieuwe unitlinks kunnen na beoordeling worden gearchiveerd; daarna daemon-reload. Git-wijzigingen gericht reverten. SSH/netwerk/sudo blijven buiten deze wijziging.

## Validatie
Unitbestanden: systemd-analyze --user verify geslaagd. Eerste status: SSH actief, NTP yes, geen failed systeemunits, circa 6.7 GiB beschikbaar RAM en 84 GiB vrije rootruimte. Hersteltests omvatten corrupte checksum, traversal en symlink/deviceweigering. Werkelijke timer- en archiveherstelresultaten worden in docs/voortgang.md vastgelegd.
