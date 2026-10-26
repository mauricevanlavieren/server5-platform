# Demo-conf toegepast — 26 oktober 2026

Opdracht: `/home/mau/demo-conf.md`. Taak `demo_conf_20261026_001`. Bestaande Server4-demo daadwerkelijk verbeterd via de bestaande SSH-route vanaf geverifieerde Server5. De huidige eigenaaropdracht autoriseert deze concrete Server4-wijziging. Bestaande vuile Server5-werkboom en andere projecten behouden. Geen echte berichten, betalingen, leveranciersacties of externe publicaties. Geen Notion-publicatie: de expliciete opdracht “publiceer niets extern” gaat hier vóór de algemene documentatieafspraak. De bestaande lokale Current Projects-kaart is bijgewerkt.

## Onderzoek en resultaat

De bestaande stdlibapp had intake, offerte/akkoord, planning en beschikbaarheid, monteursconcepten, aparte diagnose/vervolgbezoeken, voorraadreservering/verbruik, vaste-prijsbewaking, facturen en deelbetalingen. Revisies en atomische opslag bestonden al. W106 en W112 waren administratief afgesloten fictieve regressiedossiers. Onderzoek: bestaande code/README en eerdere bewijsverslagen, daarna daadwerkelijke Chromium-interface. De oude README liep achter op de implementatie en is vervangen door een actueel bedienings-/hersteloverzicht.

Gevonden en verholpen:

- Goedkeuringsvelden werden door een te brede datumherkenning onbruikbaar. Naam, datum en referentie zijn nu afzonderlijke velden, ook voor meerwerk. Historische tekstafspraken blijven behouden. Meerwerkvelden verschijnen alleen bij die afrekenvorm.
- Een vaste offerteprijs vereiste onnodig een uurtarief om een concept te maken. Het concept ontstaat nu direct uit de prijsafspraak; werkelijk materiaal en uren blijven in het dossier en worden niet dubbel opgeteld. Prijsafwijkingen blijven zichtbaar en definitief maken blijft gecontroleerd. Tariefherkomst en bestaande klant-/standaardtarieven blijven behouden.
- Nieuwe directe opdrachten vragen nu afzonderlijk klantakkoord vóór planning en gereedmelding. Dit is additief voor nieuw aangemaakte dossiers; bestaande dossiers worden niet herschreven.
- Betaling vraagt bedrag, datum, bank/kas/pin en referentie. Terugboeken bewaart de originele betaling en reden. Een herhaalde terugboeking en overbetaling worden geblokkeerd.
- Gehele/gedeeltelijke credits houden het oorspronkelijke factuurbedrag intact. Cumulatieve btw-afronding sluit bij volledige creditering exact aan op het origineel. Klanttegoed wordt afzonderlijk terugbetaald; afsluiten vereist verklaarbaar nulsaldo. Vervangend concept vereist volledig gecrediteerd en vereffend origineel, met blijvende verwijzing en archief.
- Afgesloten dossiers tonen een bruikbaar overzicht van offerte/akkoord, bezoeken, uitvoering, materiaal, factuur, betalingen, credits en historie. Afgerond is groen. Correcties beginnen met expliciet heropenen met reden. Garantie kan rechtstreeks vanuit het afgesloten dossier; bestaande eigenaarbeoordeling blijft bestaan. Open opdrachten kunnen met reden worden geannuleerd nadat materiaal/inkoop is afgehandeld.
- Deelontvangsten boeken alleen het ontvangen aantal. Ongebruikte reserveringen kunnen vrijgegeven worden. Verbruik kan retour; na facturatie is voldoende kredietreferentie vereist. Winkelretour verbindt voorraad, credit-btw en fictieve kas-terugbetaling.
- De nieuwe onderdelenroute kon het dashboard laten crashen door ontbrekende klantconceptstatus; dit is hersteld. Deelontvangsten worden nu bij de juiste opdracht teruggegeven. Afgeronde vervolgbezoeken blokkeren geen toekomstige capaciteit meer.
- Conflictherstel heeft een expliciete knop die na polling beschikbaar blijft; eigen invoer wordt niet overschreven. Schone vensters synchroniseren en gegevens blijven na herladen staan. Een revisie blokkeert dubbele verwerking van dezelfde aanvraag.
- Dashboard onderscheidt omzet excl. btw, ontvangsten incl. btw, concepten en onbekende marge. Ontvangsten volgen betaalmethoden en correcties. Grootboekexport bevat herleidbare facturen, credits, betalingen, terugboekingen en refunds; oorspronkelijke en vervangende facturen tellen niet dubbel.
- Boekhoudstatussen: nog te verwerken, export geregistreerd, handmatig bevestigd met bewijsreferentie, fout/afstemming. Download verandert niets. Nieuwe financiële correcties maken een eerdere bevestiging opnieuw afstemmingsplichtig.
- Handmatige backup/herstelutility met SHA256-manifest bewaart bron, workflow en tegelconfig. Herstel controleert alles vooraf en bewaart de actuele toestand vóór herstel. Geen authbestanden.

## Browseracceptatie

Echte headless Chromium met Playwright, bestaande HTTP-app op Server5 in een afzonderlijke kopie van de fictieve gegevens. Alle handelingen via zichtbare knoppen/formulieren; API-GETs alleen voor bedrag-/statusasserties. Geen muterende proeven op live gebruikersdata. `browser-tests.cjs`, `browser-results.json`; aanvullende correctieroute in `browser-additional.cjs` / `browser-additional-results.json`. Foutlogs/screenshots uit tussenproeven zijn niet de finale acceptatie. Een timingfout waarbij polling de herstelknop verwijderde is gevonden, gecorrigeerd en opnieuw getest.

| # | Scenario | Resultaat en bewijs |
|---|---|---|
| 1 | Nieuwe directe opdracht zonder materiaal → akkoord → planning → factuur → betaling → afsluiting | Geslaagd; €60 excl. + €12,60 btw = €72,60; dossier-afgerond.png |
| 2 | Vaste offerteprijs, afwijkende uren én werkelijk materiaal | Geslaagd; 2 uur en €25 geregistreerd materiaal blijven €100 excl. / €121 incl.; één vaste-prijsregel, geen dubbele facturatie; vaste-prijs.png |
| 3 | Offerte met afzonderlijk goedgekeurd meerwerk | Geslaagd; €100 + €25 = €125 excl.; twee regels; aparte naam/datum/referentie |
| 4 | Onderdeel ontbreekt → inkoop → deelontvangst/restontvangst → vervolg → verbruik → factuur | Geslaagd; bestelling 2, ontvangst 1+1, verbruik 1; diagnose 0,5u + vervolg 1u en €15 materiaal = €105 excl.; onderdelen-en-bezoeken.png |
| 5 | Deelbetaling en restant | Geslaagd; €20 op €72,60 → €52,60 open, restant → €0 |
| 6 | Foutieve betaling terugboeken | Geslaagd; oorspronkelijke betaling met terugboekreden behouden, €52,60 opnieuw open |
| 7 | Gedeeltelijke credit en btw | Geslaagd; €10,01 excl. + €2,10 btw; open saldo €40,49; credit-en-betalingen.png |
| 8 | Verlopen factuur, eigenaar opvolging en datum | Geslaagd; F103, verantwoordelijke Lina, 28 oktober, interne notitie; geen echte herinnering |
| 9 | Winkelverkoop en retour | Geslaagd; 3 voorraad → verkoop 2 → 1 voorraad → retour 1 → 2 voorraad; refund €12,11 incl. btw |
| 10 | Twee afzonderlijke browsercontexten, synchronisatie en conflict | Geslaagd; eerste invoer behouden, stale save geweigerd, expliciet verversen, schone sessie synchroniseert automatisch, reload behoudt gegevens; twee-vensters-conflict.png |
| extra | Afgesloten dossier heropenen → volledig credit → refund → vervangende factuur → exportstatus | Geslaagd; origineel €72,60 intact, vervanging €60,50 met verwijzing; verwerking blijft onbevestigd |

Aanvullend: `financial-tests.py` / `financial-results.json` controleren negatieve bedragen/datum, overbetaling, dubbele terugboeking, stale revisie, gesloten-dossierblokkade, cumulatieve credit-btw, replacement-ledger, historische F103 zonder dubbeltelling, W106/W112 bytegelijkheid en export zonder statusmutatie. `recovery-test.py` / `recovery-results.txt`: backup, herstel, behoud van nieuwere toestand en afwijzing van beschadigde backup in tijdelijke directories. Python compile en JavaScript syntax slagen.

## Live oplevering en screenshots

Bron op Server4: `/home/mau/server4-mobile-demo`. Gewijzigd: business.py, workflow.py, data.py, static/app.js, static/style.css, README.md. Nieuw: improvements.py en recovery.py. Bestaande app.py en static/index.html ongewijzigd meegeverifieerd. Bestaande gebruikersdienst herstart, geen nieuwe permanente service. `deployment-results.json` bewijst health en zes routes HTTP200, exacte geleverde assets en ongewijzigde live workflow.

SHA256 live workflow vóór/na: `a7ff201eefb5b4ffe25e7f2d92826435b3b4b39dedc987d5e34de5bd4ec70ee2`. W106, W112, alle overige dossiers, voorraad en historie behouden. Bestaande omzet €1045 excl. btw en open €473,40 incl. btw blijven bij oplevering behouden. Alle nieuwe testdossiers bestaan uitsluitend in de afzonderlijke testkopie.

Live Chromium-controle is read-only via een tijdelijke lokale SSH-forward: `live-browser-results.json`, `live-dashboard.png`, `live-mobiel-W112.png`. Geen echte telefoon-/microfoon- of private HTTPS-acceptatie. Visuele inspectie op desktop en 390px mobiele viewport, geen horizontale paginaoverflow; factuurregels mogen binnen hun eigen tabel scrollen. De bestaande telefoontoegangstak blijft open.

Browserhulpmiddelen zijn tijdelijk op Server5 geïnstalleerd onder /tmp en ~/.cache/ms-playwright, met benodigde systeembibliotheken via bestaande sudo. Geen SSH-, firewall-, Tailscale-, AppArmor- of Bubblewrapinstellingen gewijzigd; geen reboot. De pakketinstallatie voerde standaard herstarts van enkele ondersteunende OS-diensten uit. Hostmonitoring en bestaande backups zijn niet vervangen. Tijdelijke test-HTTP-server en SSH-forward worden na acceptatie gestopt.

## Backup en rollback

Originele bron en workflowreferentie vóór de eerste wijziging: Server4 `backups/demo_conf_20261026_001/`. Tussenstappen en eindversie eveneens geback-upt onder `demo_conf_20261026_001-final/` en `demo_conf_20261026_001-final2/`. Nieuwe complete snapshot na deployment staat in deployment-results.json. Rollback naar vóór de opdracht: vergelijk latere wijzigingen, stop bestaande demo-userdienst, herstel alleen de bestaande bronbestanden met hun relatieve paden uit de eerste backup, verwijder desgewenst uitsluitend de nieuwe modules improvements.py/recovery.py, start dienst en controleer /health en dossierbedragen. Zet workflow-reference.json niet blind terug: de bronrollback heeft geen state-restore nodig; gegevens zijn additief. Voor bewust gegevensherstel: README en recovery.py, altijd met behoud van de actuele toestand.

Server5-kaartrollback: onder bestaande writer.lock uitsluitend eigen taak/binding herstellen uit before.json, met behoud van andere projecten, used_ids en latere histories. Volledige kaarten vóór snoeien zijn automatisch gearchiveerd in docs/mindmaps/current-projects/queue.

## Beperkingen en oordeel van Henk

Praktijkproef: **ja, als afgebakende proef met fictieve gegevens en menselijke controle van financiële uitzonderingen**. Kopen / productie: **nog niet**. Nodig zijn echte accounts en toegangsrechten, gevalideerde boekhoudimport (gekozen voorbereidingsdoel e-Boekhouden.nl; mapping en proefimport nog extern te controleren), bank/mail/leveranciersintegratie waar gewenst, stabiele klant-/artikelstamgegevens, kostprijzen/loon/overhead voor marge, operationele externe backup en een juridisch/fiscaal beoordeeld factuurproces. De app gebruikt nog één gedeeld JSON-bestand en vaste demodatum; geen productiegeschikte beveiliging, meerdere serverprocessen of schaalgarantie. Legacybetalingen zonder datum/methode/referentie worden eerlijk als onbekend getoond, niet aangevuld met verzonnen bewijs. Winkelretour registreert een fictieve terugbetaling; er bestaat geen echte betaalprovideractie. Een bevestigde boekhoudstatus is handmatig bewijs, geen gecontroleerde API-koppeling. Alleen tekst/regels vormen de lokale AI; geen externe AI-acties.

## Taakadministratie

Current Projects: 4 nodes vóór → 6 tijdens → 4 na. Eigen stap en opdrachtwortel na bewijs gesnoeid, bestaande telefoonblokkade behouden. during-validation.json en final-validation.json: consistent=true, bronhash=publicatiehash, project_invariants_valid=true; done-nodes uitsluitend bladeren. Kaartstatus succeeded. Dit was een CLI-taak zonder brokerrecord; er is geen brokerresultaat of workerexit verzonnen.
