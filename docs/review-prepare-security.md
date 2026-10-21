# Review prepare-security.sh — 2026-10-21 UTC

## Status en scope
Op verzoek uitsluitend gelezen en beoordeeld: het script is NIET uitgevoerd en is ongewijzigd. Geen sudo-authenticatie, installatie, verwijdering of sandboxtest uitgevoerd tijdens deze review. Alleen documentatie/Git/Notion bijgewerkt. Exact bronpad: /home/mau/server5-commandcenter/scripts/prepare-security.sh.

## Volledige inhoud

```bash
#!/usr/bin/env bash
# User runs this in their own terminal. Never enter a password in chat.
set -euo pipefail
[[ $(hostname) == server5 ]] || { echo 'Verkeerde host'; exit 1; }
[[ $(id -u) != 0 ]] || { echo 'Start als mau, niet als root'; exit 1; }
[[ $(id -un) == mau ]] || exit 1
sudo -v
printf '%s\n' 'Installatieplan: uitsluitend bubblewrap; geen verwijderingen.'
sudo -n apt-get --simulate install bubblewrap
sudo -n apt-get --no-remove install bubblewrap
printf '%s\n' 'SSH-configuratie alleen valideren; geen reload.'
sudo -n /usr/sbin/sshd -t
printf '%s\n' 'AppArmor-status alleen lezen.'
sudo -n aa-status
printf '%s\n' 'Bubblewraptest als gewone gebruiker:'
bwrap --ro-bind / / --unshare-user --unshare-pid --proc /proc --dev /dev /bin/true
printf '%s\n' 'Basiscontrole geslaagd; meld gereed aan Codex.'
```

## Gedrag en systeemwijzigingen
1. set -euo pipefail stopt bij de meeste fouten, ontbrekende variabelen en falende pipelines. Controleert hostname server5 en gebruiker mau; weigert uid 0. Dit is een scopecontrole, geen extra beveiligingsisolatie.
2. sudo -v vraagt zo nodig het bestaande sudo-wachtwoord en vernieuwt de tijdelijke sudo-authenticatiecache volgens bestaande policy. Er worden geen sudoers-regels of permanente rechten toegevoegd. Sudo/auditlogging kan wel worden bijgewerkt.
3. sudo -n apt-get --simulate install bubblewrap toont een berekend pakketplan zonder installatie. Dit plan wordt niet automatisch op uitsluitend één nieuw pakket gecontroleerd. De simulatie vormt geen interactieve goedkeuringspoort in het script: daarna gaat het direct door.
4. sudo -n apt-get --no-remove install bubblewrap wijzigt het systeem: download/cache, pakketbestanden waaronder bwrap, dpkg/APT-status en logs. --no-remove laat APT afbreken als pakketten verwijderd zouden worden. Het blokkeert NIET extra afhankelijkheden, aanbevolen pakketten of upgrades. Geen -y: APT kan zelf om bevestiging vragen, maar dat is niet gegarandeerd voor elk plan. De tekst 'uitsluitend bubblewrap' is daarom te stellig; alleen de expliciet aangevraagde pakketnaam is beperkt. Root-maintainerscripts en triggers horen bij pakketinstallatie; effecten volgen het actuele pakketplan. Er is geen versiepin, apt update, automatische rollback of bewijs dat iedere pakkettrigger zonder service-impact is.
5. sudo -n /usr/sbin/sshd -t controleert configuratie en sleutels met rootleesrechten. Het script geeft geen opdracht om SSH-configuratie te wijzigen of sshd te reloaden/herstarten.
6. sudo -n aa-status leest AppArmor-status. Het script laadt of wijzigt geen AppArmor-profiel en verandert geen sysctl. aa-status is lokaal gevonden op /usr/sbin/aa-status.
7. bwrap draait als mau, maakt tijdelijke user-/PID-/mount-isolatie en virtuele /proc-/dev-mounts en start /bin/true met / read-only gebonden. Het verandert geen permanente hostmounts. Het is een minimale smoke-test, geen volledige Codex-sandboxtest; geen expliciete netwerkisolatie (--unshare-net ontbreekt). Als Ubuntu het benodigde usernamespacegebruik blokkeert, kan de test blijven falen na pakketinstallatie.
8. Eindmelding verschijnt alleen als voorgaande opdrachten slagen. Falen na de installatie draait die installatie NIET terug. set -e is geen transactie.

## Vereiste sudo-rechten
Start als mau, niet als root. Bestaande sudo-policy moet uitvoering als root toestaan van apt-get met de twee opgegeven argumentlijsten, /usr/sbin/sshd -t en aa-status (feitelijk /usr/sbin/aa-status). sudo -v moet authenticatie toestaan. Geen nieuwe NOPASSWD-regel nodig; een normale wachtwoordvereisende sudo-toekenning kan voldoen. -n verbiedt verdere wachtwoordprompts: bij verlopen/niet-toepasselijke cache of onvoldoende policyrechten stopt die opdracht. Deze review heeft de effectieve sudo-policy niet alsnog kunnen bewijzen en geen rechten gewijzigd. Geef nooit een wachtwoord in chat door en verleen geen generieke nieuwe root-shellrechten voor dit script.

## Risico en advies vóór latere uitvoering
Beperkt doel, maar niet gegarandeerd één pakket en niet transactioneel. De eerdere simulatie toonde alleen bubblewrap, maar die historische uitkomst is geen garantie voor een latere run. Vóór uitvoering eerst pakketplan beoordelen en nieuw geïnstalleerde/geüpgradede versies vastleggen. Overweeg een expliciete pauze/plancontrole en betere afbakening; script nu op verzoek ongewijzigd gelaten. Een specifiek AppArmor-profiel vraagt afzonderlijke beoordeling als de test faalt. Geen globale beveiligingsverlaging toepassen. De eerdere uitvoeringsuitnodiging geldt niet als opdracht om het nu te starten: de gebruiker heeft expliciet uitstel gevraagd.

## Rollback, uitsluitend voorstel — niet uitgevoerd
- Nu: geen scriptwijzigingen uitgevoerd, dus geen systeemrollback nodig.
- Alleen tijdelijke sudo-cache intrekken indien gewenst met sudo -k in dezelfde gebruikerscontext; dit herstelt pakketwijzigingen niet en kan volgende sudo-acties opnieuw om authenticatie laten vragen.
- Na latere installatie: eerst /var/log/apt/history.log, /var/log/dpkg.log en de vastgelegde voorstatus vergelijken. Als bubblewrap tevoren niet geïnstalleerd was en niet inmiddels elders nodig is: eerst sudo apt-get --simulate remove bubblewrap beoordelen. Pas na akkoord sudo apt-get remove bubblewrap uitvoeren. Niet purge/automatisch autoremove gebruiken. Dit verwijdert pakketbestanden; logs en eventuele cache blijven behouden.
- Extra nieuw geïnstalleerde afhankelijkheden alleen afzonderlijk beoordelen; geen brede opruiming. Upgrades van bestaande pakketten worden door verwijderen van bubblewrap niet teruggedraaid; daarvoor zijn eerdere versies en een apart onderhoudsplan nodig. Het huidige script bewaart die rollbackinformatie niet zelf.
- sshd -t en aa-status hebben geen configuratiewijziging om terug te draaien; tijdelijke bwrap-namespaces verdwijnen wanneer het proces eindigt.
- Een latere mislukte SSH-/AppArmor-/bwrap-controle betekent mogelijk dat bubblewrap al geïnstalleerd is. Eerst feitelijke toestand controleren; niet automatisch verwijderen.

## Reviewwijziging, validatie en herstel
Datum: 2026-10-21. Wijziging: deze review en verwijzing in voortgang toegevoegd; scriptinhoud behouden. Reden: gebruiker wil exacte inzage vóór uitvoering. Validatie: broninhoud gelezen, bronhash voor/na documentatie vergeleken, Git-diff beoordeeld; Notion-publicatie teruglezen. Risico van review beperkt tot documentatie; rollback daarvan met gerichte Git-revert. Mindmap-update voor ChatGPT: beveiligingsstatus blijft 'review gereed; script niet uitvoeren tot nieuwe opdracht'; geen architectuurwijziging.
