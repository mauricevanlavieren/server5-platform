# Voorbereiding — 2026-10-21

## Bubblewrap: voorbereid, niet geïnstalleerd
`sudo -n true` en `sudo -n -l` vragen een wachtwoord. Er is geen roottoegang in deze sessie. De APT-simulatie van `apt-get -s install bubblewrap` toont één nieuw pakket 0.9.0-1ubuntu0.3, geen verwijderingen. Geen pakketinstallatie uitgevoerd.

Vervolg met beschikbare beheerdersrechten: pakketmetadata vernieuwen, installatieplan opnieuw controleren en `sudo apt install bubblewrap` uitvoeren. Controleer `command -v bwrap`, versie en een minimale sandboxaanroep. Op Ubuntu 24.04 kan aanvullend het specifieke bwrap-userns-restrict AppArmor-profiel nodig zijn; beoordeel het profiel en pakketplan voordat het wordt geladen. Verlaag niet globaal kernel.apparmor_restrict_unprivileged_userns. Daarna Codex in een nieuwe sessie valideren; geen actieve daemon nu herstarten.

Bron: https://learn.chatgpt.com/docs/sandboxing

## Tailscale
Niet aangetroffen; /dev/net/tun bestaat; tijd gesynchroniseerd. Nog nodig: gekozen tailnet, serveridentiteit/tag, eigenaar en minimale grants, sleutelbeheer en beschikbare beheerdersrechten voor installatie. Gebruik een gecontroleerde officiële pakketbron. Voor aansluiting DNS/route-impact bepalen; standaard DNS- en routewijzigingen vermijden. Geen activering, login, subnetrouter, exit-node, Tailscale SSH of publicatie in deze fase. Huidige SSH-verbinding behouden.
Bron: https://tailscale.com/docs/install/linux

## Docker
Geen Docker/containerd-pakketten aangetroffen. Ubuntu noble/amd64 is een passende installatiebasis. Nog nodig: architectuurbesluit rootless versus rootful, pakketbron, opslagpad/backup, logrotatie, resourcebudget en poortbeleid. Installatie kan automatisch een daemon starten en bridges/firewallregels toevoegen; daarom niet uitgevoerd. Beoordeel dit vooraf. Publiceer diensten aanvankelijk alleen op loopback; geen onbeoordeelde Docker-socketmontages of toevoeging aan de docker-groep.
Bron: https://docs.docker.com/engine/install/ubuntu/

## Monitoring
Journald, rsyslog, htop en sysstat aanwezig. Geen failed systemd-units. Sysstat-collect.timer actief, maar /etc/default/sysstat bevat ENABLED=false: historische verzameling niet als werkend aannemen; controleer daadwerkelijke sar-output en collectorconfiguratie vóór activering. Geen Prometheus, node-exporter, Grafana of smartmontools aangetroffen. Begin met hostmetingen CPU/RAM/swap/disk, servicefouten, tijdsync, updates en SMART. Bepaal retentie, resourcebudget en lokale/private toegang voordat exporters starten. SMART, firewallregels en geladen AppArmor-profielen konden niet volledig zonder root worden vastgesteld. Geen nieuwe luisterpoorten geopend.

## GitOps en architectuur
Lokale repository voorbereid met branch main, zonder remote of commit. Git-identiteit ontbreekt. Nog kiezen: remote/eigenaar, gewenste branchbeveiliging, beoordelingsproces, secretopslag, gecontroleerde deploy-identiteit, backup en hersteltest. Geen credentials genereren of accounts autoriseren zonder concrete noodzaak. Begin met versiebeheer en handmatig beoordeelde Compose-configuraties; automatische reconciliatie volgt na architectuurkeuze. Kubernetes blijft uitgesteld. Bewaar inventaris lokaal; .gitignore is geen bescherming voor later geforceerd toegevoegde bestanden.

## Onderhoud
Host vraagt herstart wegens apparmor. Plan onderhoud en verifieer hersteltoegang vóór herstart; nu niet uitgevoerd. UFW-configuratie meldt ENABLED=no; effectieve firewallregels zijn zonder root niet vastgesteld. Firewall nu niet aanpassen. LVM-vrije ruimte uitsluitend als schatting beschouwen tot vgs/lvs met beheerdersrechten zijn gecontroleerd.
