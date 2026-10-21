# Mobiele AI-bediening — doelarchitectuur en plan

Datum: 2026-10-21 UTC. Status: uitsluitend planning; geen implementatie, netwerkactivatie of webpublicatie geautoriseerd in deze stap.

## Hoofddoel en gebruik
**Server 5 moet uiteindelijk volledig vanaf mijn telefoon bediend kunnen worden via een eenvoudige, beveiligde AI-chatinterface.** Eén Nederlandse chat met statuskaart, taakgeschiedenis en duidelijke knoppen voor voorstel goedkeuren, weigeren en stoppen. Dezelfde interface werkt op laptop. ChatGPT blijft het centrale aanspreekpunt voor doelen en review; Codex is de uitvoerder op server5.

De eigen commandcenter-chat is niet automatisch de officiële ChatGPT-app of een gekoppeld ChatGPT-gesprek. MVP: eigen mobiele webchat met Codex als uitvoerende AI, plus expliciete overdracht naar ChatGPT via Notion. Rechtstreekse bediening vanuit de officiële ChatGPT-app is een afzonderlijk te onderzoeken integratie, niet bewezen en geen MVP-afhankelijkheid. Geen gedeelde browsersessie, accounttokenkopie of verzonnen ChatGPT-shellkoppeling. Alle reguliere toegestane taken moeten uiteindelijk vanaf telefoon mogelijk zijn, inclusief goedkeuring; calamiteiten kunnen alsnog console/LAN-SSH vereisen.

## Feitelijke status: drie bewijsniveaus
**Werkt lokaal, eerder uitgevoerd en gecontroleerd:** Codex 0.163.0 in deze sessie op server5; Git-bron en heuristische credentialguard; vijfminuten-hostmetingen en dagelijkse configuratiebackup via usertimers; geïsoleerde hersteltest; expliciete Notion-snapshots/readback en MindMap AI-nodewijzigingen via sessieconnectoren. Dit bewijst geen onbeheerde beschikbaarheid: linger=no, backup op dezelfde SSD, geen externe alerts.

**Technische mogelijkheid onderbouwd, geen lokale end-to-end-proef:** lokale help van codex exec toont JSONL-output; codex app-server-help toont stdio/Unix-transport. Officiële OpenAI-documentatie beschrijft app-server voor conversaties, events en approvals. Tailscale-documentatie beschrijft Serve voor privé-HTTPS en identiteitsheaders. Dat is bewijs van interfaces/productmogelijkheden, niet van een werkende eigen chat, veilige worker of aanwezige Tailscale-installatie. Tijdens deze planningsstap uitsluitend --help gelezen; geen agenttaak/app-server gestart.

**Nog te bouwen/testen:** Tailscale-aansluiting en telefoon/laptoptoegang, HTTPS-route, app-authenticatie, mobiele UI, queue/taakopslag, eigen Codex-adapter, afgedwongen workerisolatie, statusstream, stop/goedkeuringsflow, crashherstel, servicecredentials voor achtergrondpublicatie, backup van nieuwe taakdata en optionele spraak. Bubblewrap/SSH-rootcontrole nog open; prepare-security.sh is alleen gereviewd, niet uitgevoerd.

## Logische architectuur
Telefoon/laptop met Tailscale → privé HTTPS via Tailscale Serve → lokale webbackend → authenticatie en autorisatie → taakopslag/queue → geïsoleerde Codex-worker via lokale stdio → server5-werkruimte.

Vanuit backend naar browser: status en geredigeerde events. Vanuit afronding: beoordeelde Markdown/Git-commit → publicatiewachtrij → Notion-snapshot/readback; relevante architectuurwijziging → MindMap AI-update. Beveiligingsbeleid wordt serverzijdig afgedwongen, niet door browser of taalmodel.

Voorkeur voor een kleine webapp met één backend en SQLite-taakopslag; taal/framework definitief kiezen bij M2 op basis van onderhouden dependencies en teamvoorkeur. Geen extra LangGraph-agent, PostgreSQL, Kubernetes of lokale grote spraak/taalmodellen nodig voor MVP. Containerisatie is optioneel, geen excuus voor Docker-sockettoegang; gewone systemd-diensten met afgebakende rechten zijn ook mogelijk. Eén uitvoerende taak tegelijk. Startbudget ter toetsing: backend 256 MiB, worker maximaal 1 GiB/2 CPU, queue maximaal 10 taken, taakdeadline standaard 15 minuten met expliciete verlenging. Deze budgetten zijn ontwerpwaarden, geen uitgevoerde configuratie.

## 1. Besloten toegang en HTTPS
Tailscale op server5 en door gebruiker beheerde telefoon/laptop, met MFA op account en alleen bevoegde identiteiten/apparaten. Nieuwe minimale grants beperken toegang tot de webdienst; geen hele tailnet vertrouwen. Exacte identiteit, tags, grants en noodzakelijke tailnetinstellingen eerst laten kiezen/bevestigen. Deze opdracht verandert geen andere apparaten of tailnetbeleid.

Tailscale Serve is de voorkeursroute voor HTTPS uitsluitend binnen het tailnet; geen Funnel, portforward, publieke reverse proxy, subnetrouter, exit-node of Tailscale SSH. Backend luistert uitsluitend op loopback of een geschikte lokale socket, nooit 0.0.0.0/LAN. Browser accepteert alleen geldig TLS met passende naam; geen certificaatwaarschuwingen wegklikken of HTTP-omweg. De interne lokale proxyhop kan loopback-HTTP zijn; toegang vanaf telefoon/laptop moet HTTPS zijn. HTTPS/MagicDNS/certificaatvoorwaarden vóór configuratie toetsen, rekening houden met eventuele vermelding van certificaatnamen in publieke certificaatlogs. LAN-IP/default route/DNS en bestaande SSH behouden; geen extra DNS-acceptatie of geaccepteerde subnetroutes.

## 2. Authenticatie en bescherming van webverzoeken
Tailscale-identiteit is de buitenste laag. Daarboven een app-eigen passkey-aanmelding (WebAuthn) met ownerrol; registratie alleen via een gecontroleerde eenmalige bootstrap na M0/M1, geen open registratie. Tweede passkey op laptop en offline herstelcodes; recovery is even sterk als de normale login. Geen credentials in Notion/Git of browser-localStorage. Korte sessies, Secure/HttpOnly/SameSite-cookies, CSRF-bescherming, Origin/Host-controle, rate limiting en herauthenticatie bij gevoelige besluiten. Gebruiker/apparaat intrekken bij telefoonverlies; bestaande sessies ongeldig maken.

Identiteitsheaders alleen vertrouwen uit de vastgestelde lokale proxyroute; headers van browsers niet als bewijs accepteren. Omdat ook andere lokale processen loopback kunnen benaderen, mag een header op zichzelf nooit schrijfautorisatie geven. App-authenticatie blijft verplicht. Chat, logs en Markdown zijn onbetrouwbare invoer: veilig renderen met HTML-sanitizing/CSP, geen uitvoerbare HTML of shellknoppen uit modeltekst. Toegang tot logs en taak-ID's per eigenaar autoriseren; geen uitlek via directe objectverwijzingen.

## 3. Codex-koppeling en uitvoeringsgrens
Voorkeur: aparte backendadapter die een eigen codex app-server-kindproces via stdio beheert; geen Codex-protocol of onbewerkt terminalkanaal in de browser. Bestaande Codex-daemon van de interactieve gebruiker niet herconfigureren of kapen. Protocolschema voor gekozen versie vastzetten en integratietests herhalen bij upgrades. app-server is in lokale help experimenteel gemarkeerd; bewijsproef is daarom een releasevoorwaarde. codex exec met JSONL is alleen alternatief voor afgebakende niet-interactieve taken, niet blind vervangen voor interactieve approvalafhandeling.

De worker krijgt bij latere inrichting een afzonderlijke niet-root service-identiteit, eigen werkruimte en officieel geauthenticeerde Codex-context; geen sudo-lidmaatschap, docker/lxd-groep, toegang tot mau/.ssh of alle privédata. Geen auth.json kopiëren om identiteit te omzeilen. Controleer vooraf of account/licentie en niet-interactief gebruik de benodigde officiële authenticatieflow ondersteunen; bij ontbrekende auth stopt de taak. API-billing en ChatGPT-abonnement niet gelijkstellen; budget en gebruik zichtbaar maken, geen kostenramingen als feiten verzinnen.

Alleen toegewezen Git-worktree(s) schrijfbaar; read-only hoststatus via een kleine expliciete adapter. Standaard geen algemene root-/netwerkbeheercommando's. De huidige Full Access-instelling is geen webworkerbeleid. Start alleen na bewezen sandbox-, filesystem- en egressgrenzen: geen sudo, host/socket-mounts of arbitrary outbound toegang. Noodzakelijke model-/connectorverbindingen apart begrenzen. AGENTS en prompts zijn aanvullende instructies, geen technische sandbox. Promptinjectie uit repository/Notion/MindMap mag geen toestemming uitbreiden.

## 4. Taakautorisatie en goedkeuring
Taakflow: ingediend → gevalideerd → gepland → wacht_op_goedkeuring → in_wachtrij → bezig → wacht_op_goedkeuring indien nieuw verzoek → geslaagd/mislukt/geannuleerd/onbekend_na_herstart. Alleen owner kan starten/goedkeuren/stoppen; een toekomstige observerrol heeft uitsluitend leesrechten.

Vaste read-only handelingen kunnen als expliciete allowlist-taak zonder extra bevestiging werken. Wijzigingen tonen eerst doel, exacte scope/paden, waar beschikbaar commando/diff, risico en rollback. Goedkeuring serverzijdig binden aan gebruiker, taak/turn/item, voorstelhash, policyversie, werkruimte en vervaltijd; niet alleen aan 'ja' in chat. Nieuwe effecten of veranderd voorstel vragen nieuwe beoordeling. Geen stilzwijgende goedkeuring bij timeout, disconnect of protocolfout; geen generieke acceptForSession-keuze in MVP. Codex approvalevents alleen accepteren voor bestaande actieve taak, met matching thread/turn/item en expliciete bevoegde beslissing.

Netwerk/SSH/firewall/sudoers, dataverwijdering, partities, andere servers en externe blootstelling vallen buiten de autonome worker. Daarvoor blokkeert de broker de taak en vraagt een apart beoordeeld onderhoudsplan; mobiele bevestiging maakt een rootactie niet vanzelf technisch veilig. Bij de eerste versie gaan privileged acties via de bestaande terminalprocedure. Een later nauw begrensde privilegehelper vereist afzonderlijk ontwerp/toestemming; nooit een root-shell achter een chatknop. Onbekende tool/permissionaanvragen fail-closed. Controleer ook daadwerkelijk uitgevoerde subprocessen: een top-level promptgoedkeuring alleen is onvoldoende tegen shellescapes of toolmisbruik.

## 5. Status, logs en lopende taken
Mobiele chat toont serveronline/statusdatum, wachtrij, actuele taak, fase, laatste activiteit/heartbeat, pending approval en eindresultaat. SSE-statusstream met eventvolgnummers en herverbinden; browser ontvangt alleen taakgebonden, geredigeerde data. Bij verbroken verbinding stopt de statusweergave met 'verbinding verbroken', niet met een verzonnen succes. Backend mag een al expliciet goedgekeurde begrensde taak voortzetten, maar nieuwe approvals blijven wachten. Stopknop onderbreekt worker; reeds uitgevoerde wijzigingen verdwijnen niet vanzelf.

Per taak: actor, opdracht, policy/voorstelhash, gebeurtenissen UTC, getoonde en goedgekeurde acties, exitstatus, gewijzigde paden, Git-commit, validatie/rollback en publicatiestatus. Geen wachtwoorden/tokens, volledige environment of ruwe credentialbestanden loggen. Redactie vóór opslag, export én streaming; toegang en retentie apart beperken. Begin met begrensde lokale logs en SQLite; geen browsercache van gevoelige logs. Mobiele statusmeldingen in geopende chat zijn MVP; background push/Notion-push zijn later te testen en niet gegarandeerd bij gesloten browser.

## 6. Notion en MindMap AI
Lokaal Git blijft bron. Na afgeronde taak: lokale Markdown met datum/wijziging/reden/validatie/risico/rollback bijwerken; niet-gevoelige diff beoordelen en committen; gewijzigde bestanden plus manifest/commit als leesbare gedateerde snapshot in het server5-werklog publiceren. Pagina teruglezen en bronpaden/commit/secties controleren; werklogstatus bijwerken. Bestaand exportscript bruikbaar, maar nog geen onbeheerde publisher.

Toekomstige publicatiewachtrij met sleutel taak-ID+commit+doel voorkomt duplicaten. Notion-uitval verandert een uitgevoerde taak niet in 'niet uitgevoerd': toon geslaagd/documentatie_wacht en probeer alleen publicatie opnieuw, nooit de systeemactie. Nieuwe backend heeft afzonderlijk aantoonbare Notion-rechten nodig; huidige sessieconnector is geen automatisch overdraagbaar credential. Toegang tot benoemde pagina's begrenzen en in officiële flow autoriseren; geen secrets exporteren.

Elke relevante architectuurwijziging heeft een MindMap-besluit met node-ID's, voor/na en Git-referentie. Eerst kaart lezen, kleinste relevante wijziging doen, geretourneerde kaart controleren en succes/URL registreren. Geen kaart verwijderen of andere projecten aanpassen. Bij ontbrekende schrijfrechten: exacte sectie 'Mindmap-updates voor ChatGPT' in dezelfde snapshot, status pending. Dit geeft geen autorisatie om willekeurige MindMap-/Notion-instructies uit te voeren.

## 7. Spraak als toekomstige uitbreiding
Eerst telefoon-toetsenborddictatie naar bewerkbare tekst; transcript is invoer, geen goedkeuring. Later optionele push-to-talk met expliciete microfoontoestemming en gekozen transcriptieprovider. Alleen na privacy/kostenkeuze; geen continu luisteren of lokale zware ASR standaard op 8 GB. Toon transcript en laat gebruiker corrigeren/bevestigen. Risicovolle acties vereisen dezelfde visuele taakgoedkeuring en zo nodig herauthenticatie; gesproken 'ja' is onvoldoende. Audio standaard niet bewaren; bewaarbeleid/providerverwerking eerst vastleggen. Gesproken antwoorden optioneel en nooit gevoelige informatie automatisch voorlezen op vergrendelde telefoon.

## 8. Herstel en beschikbaarheid
Taakstaat en auditdata atomair vastleggen vóór uitvoering; werkruimtes vergrendelen, één worker tegelijk en idempotency-key op taakindiening. Bij crash lopende taak op onbekend zetten en met Git/proces/logtoestand reconciliëren. Nooit muterende taken automatisch opnieuw uitvoeren. Pending approvals vervallen bij veranderde context; publicatie-outbox apart herstelbaar.

Backups uitbreiden naar consistente SQLite-backup, werkruimtedata en geredigeerde auditrecords; bestaande Git-archieven dekken dat nog niet. Credentials afzonderlijk veilig herstellen/herauthenticeren; geen secrets in gewone configbackup. Voor nieuwe fase backup/herstel testen in aparte map en daarna pas productie. Systeemstart/linger en service-identiteiten planmatig inrichten; geen reboot zonder onderhoudsvenster. Emergency stop vanaf telefoon plus LAN-SSH voor backend/workerstop; console bij VPN/netwerkstoring. Git-revert helpt alleen versiebeheerbare wijzigingen en draait pakketten/data/netwerk niet vanzelf terug.

## Mijlpalen met afhankelijkheden, risico en rollback
**M0 — beveiligingspoort (P0).** Afhankelijk van nieuwe uitvoeringstoestemming en eenmalige gebruikersauthenticatie. Verwerk scriptreview, beoordeel pakketplan afzonderlijk, valideer bwrap/AppArmor en sshd-config met root. Acceptatie: minimale sandbox én gerichte Codex-sandboxtest slagen, hosttoegang gelijk, privileges duidelijk. Risico pakket/profiel; rollback op werkelijk pakket-/profielverschil, geen automatische verwijdering of globale beveiligingsverlaging. Huidige status: open; niets uitvoeren.

**M1 — toegang telefoon/laptop (P0, na M0 en nieuwe uitvoeringsopdracht).** Tailscale-identiteit/grants/HTTPS-plan beoordelen, daarna pas server5 aansluiten en gebruiker begeleidt eigen clients. Acceptatie: beide clients toegelaten, onbevoegde client geweigerd, LAN-SSH/routes/DNS gelijk; geen Funnel/subnet/exit/TS-SSH. Risico toegang; rollback via behouden LAN-pad, geen routerwijziging. Geen webpublicatie in deze mijlpaal.

**M2 — backend/auth en UI-prototype (P1, na M0; uitvoeringsopdracht nodig).** Kleine app/SQLite en mobiele mockflow; eerst zonder uitvoerende Codex en zonder bereikbare publicatie. Passkeys/recovery/rollen, XSS/CSRF/Origin en taak-ID-isolatie testen. Acceptatie: geweigerde ongeldige sessies/requests en bruikbaar scherm op telefoonformaat. Risico auth-/renderbugs; rollback nieuwe app stoppen, data bewaren. Browserframework en dependencies pas hier vaststellen.

**M3 — adapterbewijs (P1, na M0/M2).** Eigen beperkte service-identiteit, sandbox en schema; read-only taak uitvoeren via stdio-adapter, approval decline/timeout/stop testen in testworktree. Acceptatie: geen lees/schrijftoegang buiten scope, geen privilege- of netwerkescape, geen agenttaak bij afgewezen voorstel. Risico code-uitvoering; stop worker en beoordeel testdiff. Geen automatische rootacties. Bij onhaalbare technische isolatie geen muterende chat vrijgeven.

**M4 — privé-HTTPS-read-only pilot (P1, na M1/M2/M3).** Pas na controle en expliciete vrijgave van publicatie een uitsluitend besloten HTTPS-route aanzetten. Telefoon via mobiel netwerk en laptop testen, directe LAN-backendtoegang onmogelijk, geldige TLS/passkeylogin, statusstreamherstel en toegangsintrekking. Risico endpointblootstelling; route/backend stoppen via LAN, geen firewallflush. Geen poort-/proxycommando's nu uitvoeren.

**M5 — gecontroleerde wijzigingen (P1, na M4).** Beperkte niet-root documentatietaak: plan/diff → approval → uitvoering → test → commit. Acceptatie: voorstelwijziging/replay/andere gebruiker/timeout weigeren; annuleren en crash zonder dubbele uitvoering; hersteldiff reproduceerbaar. Risico verkeerde taak; worker stoppen, uitsluitend beoordeelde wijziging terugzetten. Geen data wissen voor de test.

**M6 — documentatie en architectuurupdates (P1, na M5).** Publisher met eigen beperkte connectorrechten en outbox, Notion-readback, MindMap-nodes, foutafhandeling en secretsredactie. Acceptatie: taakcommit en gewijzigde Markdown terugvindbaar; connectoruitval geeft pending en retry veroorzaakt geen nieuwe uitvoering. Risico gegevenslek/duplicatie; publisher pauzeren, audit/snapshots behouden.

**M7 — productieacceptatie vanaf telefoon (P1, na M6).** Consistente backup/herstel, service-start na geplande reboot, verloren telefoon/sessie-intrekking, stop en noodherstel testen. Acceptatie: complete proef vanaf telefoon met voorstel, goedkeuring, log, Notion-snapshot, MindMap-wijziging waar relevant en herstel zonder productieschade. Werkt ook na browserherverbinden; backup buiten dezelfde SSD gepland en vervolgens getest. Risico beschikbaarheid; alleen gepland onderhoud met console/LAN-herstel. MVP gereed pas na deze bewijzen.

**M8 — spraak (P2, na M7).** Dictatie eerst; later optionele transcriptie en voorlezen na privacy/kostenkeuze. Acceptatie: transcriptbewerkingen, foutieve herkenning en weigering leiden niet tot ongeautoriseerde uitvoering. Rollback spraakfunctie uitzetten; tekstchat blijft werken.

## Open besluiten vóór bouw
Tailnet/account en minimale grants; gewenste telefoonbrowser/OS (bij eerste UI-test vaststellen); passkeyrecovery en service-identiteit; account-/licentieflow voor Codex-worker; definitieve kleine webstack; bewaartermijn en backupbestemming; connectorauth voor backgroundpublicatie. Geen van deze keuzes blokkeert dit plan, maar uitvoering moet afhankelijkheden expliciet oplossen. Geen aanvullende installaties of accounts voor deze planningsopdracht.

## Validatie, risico en rollback van deze wijziging
2026-10-21: hoofddoel toegevoegd aan hoofdplan, dit architectuurplan opgesteld en voortgang/samenwerkingsdocumentatie gekoppeld. Bronnen en lokale --help gecontroleerd; geen end-to-end-integratie geclaimd. Validatie: gerichte Markdown/Git-diff, bronpaden en Notion-readback; relevante MindMap-nodes gecontroleerd in writeresultaat. Risico uitsluitend documentatie; rollback via gerichte Git-revert en corrigerende Notion/MindMap-update, historische snapshots bewaren. Geen scripts, pakketten, diensten, authenticatie- of netwerkinstellingen gewijzigd.

## Bronnen en bewijsgrens
- OpenAI: https://learn.chatgpt.com/docs/app-server — lokale transporten, events en approvals; ontwerpkeuze, geen eigen adaptertest.
- OpenAI: https://developers.openai.com/blog/codex-as-a-platform — integratieopties exec/SDK/app-server.
- Tailscale: https://tailscale.com/docs/reference/tailscale-cli/serve — besloten HTTPS-route als productmogelijkheid.
- Tailscale: https://tailscale.com/docs/reference/examples/serve — backend alleen lokaal en vertrouwen in identityheaders begrenzen.
- Lokaal gelezen: codex exec --help en codex app-server --help (0.163.0). Geen agentturn gestart.
