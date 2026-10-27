# Server4 — demo-conf praktijkproef, 27 oktober 2026

Werkende wijzigingen geleverd en bestaande app op Server4 bijgewerkt. Eigenaar heeft Server4-uitvoering expliciet bevestigd. Taak `demo_conf_pilot_20261027_004`; uitvoering via Server5 en de bestaande strikt geverifieerde SSH-route. Hostnamen gecontroleerd; Server4 heeft geen Git-repository. Bestaande Server5-wijzigingen zijn behouden. Requirements: requirements.md (kopie van de huidige demo-conf.md).

## Oordeel

| Gebruik | Oordeel | Nog nodig |
|---|---|---|
| Verkoopdemo | Geschikt voor fictieve demonstraties; drie klantreizen geslaagd | Eigenaar activeren om live weer aan te melden |
| Begeleide praktijkproef | Technische fictieve proef met echte rollen beschikbaar en geïsoleerd getest | Eerste eigenaar/medewerkers inrichten en samen accepteren; echte gegevens wachten op externe backup, migratie-/privacy-/beheerafspraken |
| Productiegebruik | Niet gereed | Externe backup/herstelbeleid, boekhoudimportbewijs, operationele/commerciële afspraken en beveiligingsbeoordeling voor echte data |

Geen prijzen, supportbeloftes, externe integraties of productiegaranties verzonnen. Geen echte berichten, bestellingen of betalingen uitgevoerd. Geen externe publicatie; de actuele demo-conf.md verbiedt dat, dus geen Notion-publicatie of -teruglezing geclaimd. Lokale Current Projects-kaart en lokale Markdown/Git bevatten het bewijs.

## Implementatie versus informatie

| Onderwerp | Werkelijke implementatie en bewijs | Open / vereiste toegang of beslissing |
|---|---|---|
| Accounts/rechten | Flask/Werkzeug scrypt, intrekbare SQLite-sessies, CSRF en serverautorisatie; security.py, secure_app.py; unit-results.txt en pilot-browser-results.json | Eigenaar activeert eigen account; medewerkersacceptatie, productiebeoordeling, beheer en privacyafspraken |
| Monteur | Uitsluitend eigen medewerkerdossiers/uren/materiaal; beperkt readmodel en eigen werkplek; directe verzoeken naar betalingen/tarieven/gebruikers en vreemde dossiers geweigerd | Geen aparte automatische service; toewijzing via bestaande planning, gebruikerskoppeling door eigenaar |
| Administratie/eigenaar | Administratie factureert/ontvangt/exporteert; tarieven, gebruikers en financiële correcties vereisen eigenaar. Echte drie-rollenoverdracht HTTP getest tot betaald/afgesloten | Volledige oude werkplek kan eigenaaracties tonen aan administratie; server weigert deze. Eigenaar controleert onbekende materiaalprijzen vóór facturatie |
| Herleidbaarheid | Echte actor, bedrijfsdatum en werkelijk UTC-tijdstip in dezelfde atomaire workflowhistorie; aparte accountaudit. Nieuwe facturen/verkoop/retouren bewaren registratiestempel; CSV recorded_at | Oude demohistorie blijft oud; geen gebruiker of registratietijd achteraf verzonnen |
| Backup/herstel | Consistente workflow, SQLite online backup, bron/tegelconfig/sessiesleutel; geïsoleerd herstel met identieke bedrijfshistorie en controletotalen op Server5 én Server4; live-restore-results.json | Externe kopie niet uitgevoerd. Geautoriseerde externe mount, frequentie/retentie/eigenaar en hersteldoelen ontbreken. Hulpmiddel voor gecontroleerde kopie naar andere filesystem/mount beschikbaar |
| Boekhouding | /api/reconciliation vergelijkt omzet na credits, debiteuren en netto geld met document-/geldregels; referenties, bedragen en ontbrekende datums/bronvelden worden gemeld | 19 bestaande bronproblemen zichtbaar; externe import niet gevalideerd. Bevestigde mappings, doelpakket/testtenant en teruggelezen importbewijs ontbreken |
| Overstappen | Gecontroleerde JSON-proefimport voor klanten, artikelen/prijzen, voorraad en resterende beginsaldi; hash/revisiegebonden preview, regelfouten, mogelijke duplicaten, herhaalbeveiliging en historie | Alleen fictieve EUR/21%-gegevens, geen volledige historische migratie. Echte bronmapping, migratiebegeleiding, cutover en toestemming ontbreken |
| Aanschaf | /praktijkproef op bewijs bijgewerkt; ontbrekende afspraken zichtbaar. Afzonderlijke aankoopbeslissingen.md | Inrichting/periodieke prijs, functies/koppelingen in contract, training/migratie, contact/support/onderhoud, hosting/backupverantwoordelijkheid, looptijd/opzegging en uitvoerafspraken door producteigenaar te bepalen |

## Tests en browserresultaten

Acht gerichte automatische testgroepen geslaagd (unit-results.txt): niet-ingelogde/direct ongeoorloofde toegang, actor/audit/herhaling/afmelden/intrekking, administratiegrenzen/revisieconflict, eerste eigenaar/cookieflags, migratievalidatie/duplicaten/beginsaldi, herstelintegriteit/corruptieweigering, echte drie-rollenoverdracht tot factuur/betaling/afsluiting, financiële afwijkingsdetectie. Extra bestaande financiële controles geslaagd: deelbetalingen/terugboekingen, btw op gedeeltelijke en volledige credits, refunds, vervangende facturen zonder dubbeltelling, afsluiten/heropenen, materiaalvrijgave/retour, deelontvangst en herhaling. Zie financial-results.json en finance-extra-results.json.

| Browserproef | Resultaat | Bewijs |
|---|---|---|
| Offerte → akkoord → planning → uitvoering/materiaal → factuur → betaling → afsluiting | Geslaagd | journey-results.json, reis-A-afgesloten.png |
| Onderdeelbehoefte → inkoop → 2+2 deellevering → vervolgbezoek → factuur | Geslaagd | journey-results.json, reis-B-open-bestelrestant.png, reis-B-gefactureerd.png |
| Winkelverkoop → gedeeltelijke retour → fictieve terugbetaling/voorraad | Geslaagd | journey-results.json, reis-C-retourhistorie.png |
| Nieuwe oefenronde bewaart eerdere historie | Geslaagd | journey-results.json |
| Twee afzonderlijke vensters, conflict met invoerbehoud, synchronisatie/herladen | Geslaagd | collaboration-results.json, window-identities.json, screenshots |
| Verloren antwoord en tijdelijke opslagfout | Geslaagd | collaboration-results.json; geen dubbele opslag na herhalen |
| Aanmelden, gebruiker aanmaken, monteurwerk opslaan met dubbelklik/herladen, toegang intrekken | Geslaagd | pilot-browser-results.json, pilot-monteur.png |
| Importpreview met fout, verwerken, dubbelklik/herhaling, catalogus en afstemming | Geslaagd | pilot-browser-results.json, pilot-import-preview.png, pilot-import-verwerkt.png |
| Administratiesessie, geweigerd gebruikersbeheer en afmelden | Geslaagd | pilot-browser-results.json |
| Nieuwe werkplek op 390 pixels | Geslaagd | pilot-mobile-390.png; geen horizontale paginaoverloop |
| Live aanmeldpagina/assets/401 op beschermde API’s, 1366/390 pixels | Geslaagd | live-browser-results.json, live-login-1366.png, live-login-390.png |
| Live gebruikersacceptatie na eigenaarsactivering | Niet getest | Geen live testaccount of standaardwachtwoord aangemaakt; eigenaar moet zelf activeren |
| Fysieke telefoon/spraak en echte private HTTPS | Niet getest | Bestaande telefoonrouteblokkade buiten deze uitvoering behouden |
| Externe boekhoudimport en externe backupherstelproef | Geblokkeerd door ontbrekende omgeving/bestemming | Geen externe toegang, identiteit of opslag verzonnen |

Bedrijfsroutes draaiden in echte Chromium/Playwright-browsers tegen de nieuwe geauthenticeerde app met fictieve accounts en een afzonderlijke kopie van live bedrijfsstaat. De twee vensters waren afzonderlijke Chromium-vensters op Xvfb, geen fysieke apparaten. Muterende browserproeven zijn niet op live dossiers uitgevoerd. Live acceptatie is begrensd tot aanmeldpagina/toegangsweigering en gelijkheid van bron/staat. step-reconciliation.jsonl bewaart de financiële/voorraadcontroles tijdens browserproeven.

De historische demorolkeuze binnen de eigenaarsdemo is presentatie. De echte user actor blijft de ingelogde eigenaar; autorisatie gebruikt uitsluitend het echte account. Aanvullend bewijst test_real_roles_handoff_to_invoice_payment_close de overdracht eigenaar → monteur → administratie met verschillende echte accounts, vastgelegd eigenaarstarief, factuur €72,60, betaling en afsluiting.

## Herstel en financiële controle

Live workflow vóór/na bron-/dienstwijziging byte-identiek, SHA256 `4772b51acd7adca63ceab519c28744e7c9d8f157344b1a3eaca18b4aa5299f56`. Geen bestaande dossiers, historie, voorraden, facturen, credits of betalingen vervangen. deployment-results.json: dienst active, authenticatie actief, ongeauthenticeerde bedrijfs-API’s 401.

Nieuwe live backup: `/home/mau/server4-mobile-demo/backups/snapshot-20261027T145845990170Z/`, 27 bestanden. Accounts en sessiesleutel blijven uitsluitend in de afgeschermde Server4-state/backup; geen authdatabase, wachtwoord of sleutel in Git, Notion of dit verslag. Codex/SSH-loginbestanden zijn niet gekopieerd of gewijzigd.

Deze snapshot is op Server4 in een tijdelijke app/state hersteld. Dossiers/historie/voorraad/reserveringen en financiële staat waren byte-identiek; exporthash gelijk. 11 dossiers, 138 historie-items, 6 reserveringen en 10 actuele facturen gecontroleerd. Vooraf bestaande nieuwere testdoeldata zijn eerst bewaard. Geen live restore. Controletotalen vóór/na: netto omzet €1.030,00; netto ontvangen €772,90; debiteuren €473,40. live-restore-results.json. De aanvullende hersteltest met drie fictieve accounts bewijst terugzetten van gebruikers, behouden credentials en intrekken van oude sessies; recovery-evidence.json. De live snapshot had nog nul gebruikers vóór eigenaaractivering. Maak opnieuw een backup nadat echte proefaccounts zijn ingericht.

Manifestcontrole weigert gewijzigde backupbestanden vóór schrijven; manifest is een checksumcontrole, geen onafhankelijke authenticiteitsverklaring. Backups bevatten vertrouwelijke appcredentials en vereisen afgeschermde opslag. De workflow is één atomaire bedrijfstoestand, auth-SQLite heeft eigen consistente transacties; geen algemene transactie over beide opslagformaten. Eén schrijfproces ondersteund.

Beginsaldi uit proefimport worden als opening_balance geëxporteerd en tellen mee bij debiteuren, niet bij nieuwe omzet/ontvangsten. Het opgeslagen importregister toont bron-ID’s, klanten, artikelen/prijzen en aantallen. Alleen bestaand geprijsd/gecontroleerd materiaal gaat automatisch door; onbekende gegevens worden niet als nul of verkoopafspraak ingevuld. Externe importvalidatie blijft expliciet ‘niet gevalideerd’, ook wanneer balanced=true. De bestaande 19 bronproblemen zijn geen rekenverschillen; ontbrekende historische factuurdatums/betaalbronnen moeten met werkelijk bewijs worden aangevuld.

## Bestanden, dienst en rollback

Server4: nieuwe secure_app.py, security.py, pilot.py, requirements.txt, migratieformaat.md, aankoopbeslissingen.md, static/login.html/login.js en static/pilot.html/pilot.js. Gewijzigd: business.py, workflow.py, data.py, improvements.py, recovery.py, README.md, static/app.js/style.css/index.html/praktijkproef.html. De oude app.py blijft als historische bron; de bestaande dienst start secure_app.py via de nieuwe venv en één ExecStart-drop-in. Flask 3.1.3, Werkzeug 3.1.9, Waitress 3.0.2 plus gepinde afhankelijkheden; geen systeem-Python vervangen. Geen nieuwe service/scheduler, rootrechten, netwerk-/firewall-/SSH-mutatie, publieke route of reboot. Bestaande monitoring/backups behouden; nieuwe applicatiegegevens in recovery-backup opgenomen.

Herstelpunt oorspronkelijke bronnen: `/home/mau/server4-mobile-demo/backups/demo_conf_pilot_20261027_004/`. Serviceconfig vóór wijziging: service-before.txt daar. Nieuwe drop-in: `~/.config/systemd/user/server4-mobile-demo.service.d/10-pilot.conf`. UI-nacontrole bewaart de eerste nieuwe pilot.js onder post-review/static/pilot.js. Bronhashes van de finale versie: deployment-results.json/ui-final-deployment.json.

Bronrollback uitsluitend na controle op latere wijzigingen: stop bestaande dienst, herstel gewijzigde oude bronbestanden uit het herstelpunt, verwijder uitsluitend deze nieuwe bestanden als er geen latere wijzigingen zijn, verwijder uitsluitend de eigen 10-pilot.conf-drop-in, daemon-reload en start dezelfde dienst. **Geen workflow- of accountrestore als onderdeel van bronrollback.** Teruggaan naar de oude app schakelt appauth uit en herstelt de oude tunnel-/demogrenzen; doe dit alleen bewust. Na nieuwe proefimports met beginsaldi geen blinde rollback naar oudere code: oudere versies begrijpen de nieuwe omzetafbakening niet. Herstel dan een compatibele nieuwe bronversie of maak een gecontroleerd gegevensplan. Geen nieuwere historie overschrijven.

Voor dataherstel: eerst dienst stoppen, snapshot/nieuwere historie beoordelen en geïsoleerd controleren. recovery.py weigert live herstel zolang de dienst actief is, controleert alle paden/checksums vóór schrijven en maakt eerst een before-restore-kopie. Overwrite van nieuwere bedrijfsdata blijft een aparte bewust te autoriseren stap.

## Resterende gebruikershandelingen

1. Open de demo opnieuw. Onder Eerste eigenaar inrichten: lees lokaal op Server4 `cat ~/.local/state/server4-mobile-demo/owner-activation`, voer die eenmalige code in en kies zelf een wachtwoord. Deel de code of het wachtwoord niet in chat. Activeer en meld aan.
2. Open Account, rechten en praktijkproef; maak monteur-/administratieaccounts, koppel monteurs aan Bram/Noor/Lina, accepteer de werkoverdracht samen en maak opnieuw een lokale backup.
3. Producteigenaar vult aankoopbeslissingen.md in. Lever desgewenst afzonderlijk een geautoriseerde externe backupbestemming en boekhoudtestomgeving/mappings; pas dan kunnen externe herstel- en importbewijzen worden geleverd.
4. Houd echte bedrijfsgegevens en productieafhankelijkheid buiten deze fictieve proef tot de open voorwaarden zijn ingevuld en geaccepteerd.

Taakadministratie: CLI zonder brokerrecord; uitsluitend kaartmetadata bijgewerkt, geen brokerstatus vervalst. Nodes 4 vóór → 6 tijdens → 4 na. Eigen taak na bewezen oplevering gesnoeid; bestaande telefoonblokkade behouden. Eindvalidator en gepubliceerde bron worden in final-validation.json/publication-check.json vastgelegd. Taakstatus: Succeeded voor de geleverde onafhankelijke uitvoering; de hierboven genoemde externe/operationele/commerciële grenzen zijn daarmee niet opgelost.

Tijdelijke Server5-testservice, eigen SSH-testforward en Xvfb-display zijn na controle gestopt. De bestaande Server4-dienst blijft actief. Technische referenties: [Flask sessie- en cookiebeveiliging](https://flask.palletsprojects.com/en/stable/web-security/) en [Werkzeug wachtwoordhashing](https://werkzeug.palletsprojects.com/en/stable/utils/). Bronwijzigingen zijn ook afzonderlijk leesbaar in changes.diff.
