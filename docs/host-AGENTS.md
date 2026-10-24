# Server5 — experimenteel mobiel AI-commandocentrum

## Actuele opdracht en voorrang — 2026-10-21
Server5 is expliciet een experimentele speeltuin. Bouw een werkende mobiele MVP: telefoon/laptop → private Tailscale/HTTPS-toegang → mobiele webchat → lokale taakbroker → Codex-worker. ChatGPT is aanspreekpunt voor planning/review; Codex voert uit. De gebruiker autoriseert lokale omkeerbare uitvoering en sudo/root waar nodig. Dit vervangt eerdere planning-only-, M0- en sandboxvoorwaarden. Bubblewrap/AppArmor is GEEN voortgangsvoorwaarde; onderzoek of wijzig die niet verder tenzij opnieuw gevraagd. Bestaande conceptprofielen blijven als historisch onderzoek, niet actief laden.

## Host en beheerbron
Werk uitsluitend op server5 (Dell OptiPlex 5070, Ubuntu 24.04.5, i7-8700, circa 8 GB RAM). Bron: /home/mau/server5-commandcenter. Controleer hostname en Git-status vóór wijzigingen. Hergebruik Node/Python/Codex, hostmonitoring en backups; geen onnodige herinstallatie, containerstack of Kubernetes nodig voor deze MVP.

## Autonomie en grenzen
- Lokale uitvoeringsvrijheid geldt uitsluitend voor server5. Router, switch, servers1–4 en overige externe systemen niet wijzigen zonder afzonderlijke toestemming. Documentatie in het benoemde Notion-werklog en de bestaande server5-mindmap is expliciet geautoriseerd.
- Gebruik bestaande sudo-rechten. Als interactieve authenticatie ontbreekt, laat gebruiker alleen de concrete benodigde handeling in eigen terminal uitvoeren. Geen wachtwoorden vragen/opslaan of authenticatie omzeilen; geen automatische nieuwe sudoers/NOPASSWD-regels.
- Vermijd publieke internetblootstelling. Geen Funnel, publieke poortforward of ongevraagde externe infrastructuur. Tailscale-login vereist identiteit van gebruiker; geen onbekend account aannemen.
- Voorkom verlies van LAN-SSH. Voor ingrijpende netwerk-, firewall- of SSH-wijzigingen eerst herstelpad vastleggen; bestaande verbinding behouden. Geen ongeplande reboot.
- Vraag vooraf toestemming bij onomkeerbare gegevensvernietiging. Bewaar bestaande gegevens en histories; opruimen van eigen tijdelijke testartefacten mag binnen de testscope.
- Laat bestaande beveiligingsinstellingen intact waar ze niet hinderen. De MVP-worker mag volgens deze opdracht zonder Bubblewrap draaien met expliciet danger-full-access; dat biedt GEEN technische host-/filesystemisolatie. Draai webservice niet standaard als root en vergroot rootrechten niet permanent.
- Geen secrets/tokens/private sleutels/authbestanden in Git of Notion. Worker gebruikt bestaande lokale Codex-login zonder authbestand te kopiëren. Schakel externe apps/MCP in de MVP-worker uit waar ondersteund; externe veranderingen blijven apart geautoriseerd.

## Werkwijze en bewijs
Test de hele keten lokaal vóór private mobiele toegang. Onderscheid echte Codex-proeven van mocktests, lokale HTTP van werkende private HTTPS en geplande functies van implementatie. Eén uitvoerende taak tegelijk, meerdere taken persistent bewaren, cancellation en onbekende status na crash afhandelen zonder muterende taken automatisch te herhalen.
Leg wijzigingen, reden, tests, risico, rollback en resterende gebruikershandelingen vast in lokale Markdown/Git. Publiceer geactualiseerde documentatie als gedateerde Notion-snapshot en lees terug; werk centraal werklog en relevante MindMap-nodes bij. Geen claim van onbeheerde Notion-publicatie of directe officiële ChatGPT-app-shelltoegang zonder bewezen integratie. Monitoring/backups blijven behouden; breid herstel uit naar nieuwe taakdata.
