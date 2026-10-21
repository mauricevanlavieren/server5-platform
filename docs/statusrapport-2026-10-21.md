# Statusrapport server5 — 21 oktober 2026 UTC

## Uitkomst
Lokale inventarisatie en beheerbasis afgerond. Twee Codex-waarschuwingen verklaard. Bubblewrap-herstel vereist beheerdersrechten die deze sessie niet heeft; geen beveiligingsinstellingen omzeild. MCP niet geautoriseerd.

## Systeem en capaciteit
- Host server5; Dell OptiPlex 5070, Ubuntu 24.04.5 LTS, kernel 6.8.0-147-generic. Wijkt af van opgegeven 5050/24.04.4; geen identiteit gewijzigd.
- Intel i7-8700, 6 cores/12 threads; 7.5 GiB RAM (circa 6.6 GiB beschikbaar bij meting), 4 GiB swap. Intel UHD 630, geen discrete GPU aangetroffen via lspci.
- Eén SATA SSD SPCC Solid State 238.5 GiB; EFI 1 GiB, boot 2 GiB, LVM-partitie 235.4 GiB. Root-LV 100 GiB; ext4 circa 98 GiB, 85 GiB beschikbaar. Mogelijk resterende VG-ruimte, niet bevestigd: pvs/vgs/lvs geweigerd zonder root. Geen SMART-status vastgesteld en geen opslag gewijzigd.

## Netwerk en rechten
- eno1: 192.168.1.245/24 via DHCP; gateway/DNS 192.168.1.1, zoekdomein home; alleen link-local IPv6 aangetroffen naast loopback.
- SSH luistert op IPv4/IPv6 poort 22; lokale resolver poort 53 en Codex op loopbackpoort 40749 bij meting. Geen nieuwe poorten geopend.
- systemd-networkd en systemd-resolved actief; NTP gesynchroniseerd, UTC.
- UFW-configuratie ENABLED=no ondanks enabled unit; effectieve nftables/iptables-regels niet met root uitgelezen, dus geen volledige uitspraak over firewallbescherming.
- Gebruiker mau uid 1000; groepen adm, cdrom, sudo, dip, plugdev, lxd. Lxd-groepslidmaatschap is relevant bij toekomstige daemoninstallatie; geen privileges via die weg gebruikt.
- root en mau hebben een login-shell; nobody is nologin. .ssh mode 700 en authorized_keys 600. Geen sleutelinhoud gelezen.
- `sudo -n true` en `sudo -n -l`: password is required. Geen algemene wachtwoordloze sudo beschikbaar; eventuele specifieke regels konden niet worden opgesomd. Sudo-configuratie ongewijzigd.

## Software en gezondheid
Codex CLI 0.163.0, Node via nvm 22.23.3, npm 10.9.9; daarnaast distro-Node 18.19.1/npm 9.2.0 geïnstalleerd. Git, curl, jq, Python 3, htop, sysstat, OpenSSH, AppArmor, UFW en unattended-upgrades aanwezig. Geen snaps. Geen aangetroffen Docker, containerd, Tailscale, Kubernetes, Prometheus, node-exporter of Grafana als hostinstallatie; volledige dpkg-lijst lokaal opgeslagen. Geen failed systemd-units. Herstartmelding aanwezig wegens apparmor; niet herstart. Sysstat-timer actief maar ENABLED=false; werking historie nog verifiëren.

## Codex-waarschuwingen
1. daemon.stderr.log 05:08:21 UTC bevestigt bwrap ontbreekt op PATH en dat Codex de meegeleverde helper gebruikt. apt-cache: bubblewrap niet geïnstalleerd, kandidaat 0.9.0-1ubuntu0.3. Meegeleverde helper gevonden en versieaanroep werkt; minimale sandboxtest faalt met `bwrap: setting up uid map: Permission denied`. kernel.apparmor_restrict_unprivileged_userns=1; user.max_user_namespaces=30317. AppArmor kan bijdragen, maar precieze oorzaak zonder verdere rootdiagnostiek niet bewezen. Geen specifiek bwrap-profielbestand aangetroffen onder de gecontroleerde namen; geladen profielen niet leesbaar. Geen PATH-symlink als schijnoplossing toegevoegd. Installatiesimulatie veilig: 1 nieuw pakket, 0 verwijderd; echte installatie geblokkeerd door ontbrekende sudo.
2. Logregels 05:08:32 en 05:09:26 UTC identificeren de tldraw-plugin: Bearer resource metadata op https://codex-app.tldraw.xyz/.well-known/oauth-protected-resource/mcp en scopes openid profile email offline_access. De lokale plugin is app-6ab242dbeb5c8191ba5277534ef0c570/tldraw. `codex mcp list` bevat geen handmatig geconfigureerde servers; pluginservers staan niet noodzakelijk in die lijst. Geen login/OAuth, toestemming, verwijdering of configuratiewijziging uitgevoerd.

## Uitgevoerde wijzigingen en herstel
- /home/mau/AGENTS.md nieuw: rol, voorgestelde architectuur, werkwijze en expliciete veiligheidsgrenzen.
- /home/mau/server5-commandcenter nieuw: README, verwijzende AGENTS.md, docs/, plans/, inventory/, scripts/ en .gitignore; lokale Git-repository op main, zonder remote of commit.
- Inventaris en geselecteerde waarschuwingregels lokaal opgeslagen; geen auth.json, tokens of private sleutels gekopieerd. Interne netwerkgegevens staan in lokaal genegeerde inventory/.
- Geen OS-pakketten geïnstalleerd; geen SSH-, firewall-, netwerk-, sudo- of externe configuratie gewijzigd. Geen data verwijderd, diensten uitgerold of host herstart.
Herstel: de nieuw gemaakte beheerbestanden/repository hebben geen runtime-effect. Indien ongewenst kunnen deze na beoordeling worden gearchiveerd. Geen systeemrollback nodig.

## Beperkingen en vervolg
Rootcontrole nodig voor effectieve firewall, sudo-regels, SMART, LVM-vrije ruimte en AppArmor-diagnostiek. Bubblewrap daarna installeren en sandbox daadwerkelijk testen. Architectuurkeuzes en voorbereiding voor Tailscale/Docker/monitoring/GitOps staan in ../plans/voorbereiding.md. Er is geen productieklare AI-stack uitgerold.

## Bronnen
- Officiële OpenAI-documentatie: https://learn.chatgpt.com/docs/sandboxing
- MCP en pluginservers: https://learn.chatgpt.com/docs/extend/mcp?surface=cli
- Tailscale: https://tailscale.com/docs/install/linux
- Docker Ubuntu en firewallimpact: https://docs.docker.com/engine/install/ubuntu/
- Lokaal bewijs: ../inventory/ (incl. volledige pakketlijst, services, opslag, netwerk, rechten en waarschuwingen).
