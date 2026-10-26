# Henk-werkplek — ronde 3, 26 oktober 2026

**Uitgevoerd en gecontroleerd.** Opdracht: de nieuwste demo-conf.md, bewaard als requirements.md. Taak `demo_conf_operations_20261026_003`. Bestaande Server4-app aangepast via de bestaande SSH-route vanaf geverifieerde Server5. Andere hosts, authenticatie en netwerkconfiguratie niet gewijzigd. Geen echte bestellingen, berichten, betalingen of externe publicaties. Bestaande Server5-wijzigingen behouden; lokale Current Projects-kaart bijgewerkt.

## Wat is verbeterd

- **Eén compact dossier.** Eén samenvatting met status, verantwoordelijke, afspraak, bedragen en één primaire actie. Details staan onder Uitvoering en materiaal, Documenten en boekhouding, Betalingen en correcties, en Historie. De primaire actie opent het juiste formulier en brengt het relevante invoerveld in beeld. Bij een vaste prijs wordt direct het conceptformulier geopend. De mobiele primaire actie is aantoonbaar binnen de eerste schermhoogte bereikbaar.
- **Menselijke namen.** Knoppen verwijzen naar ‘Betaling van €101,25’ in plaats van een legacy-nummer. Datum en referentie ondersteunen de keuze. Interne sleutels staan in technische details. Reserveren, verbruiken en vrijgeven hebben eveneens inhoudelijke knopnamen.
- **Afhandelbare betaalwaarschuwingen.** Alleen niet-teruggeboekte betalingen met ontbrekende of onbevestigde bronnen tellen als actieve problemen. De oorspronkelijke onvolledigheid van een teruggeboekte betaling blijft in Historie. Een waarschuwing opent rechtstreeks de juiste betaalregistratie; na aantoonbaar herstel verdwijnt die waarschuwing. Ook eerdere facturen bij een vervangend concept en oude demofacturen zijn bereikbaar.
- **Bedrag → registratie → herstel.** ‘Methode niet vastgelegd’ opent een gefilterde lijst met exact de bijbehorende actieve betalingen. Metadata aanvullen verandert geen bedrag en kan bij een financieel gesloten dossier; een bedrag terugboeken vereist expliciet heropenen. Een nieuwe betaling blijft een aparte handeling. Een bestaande contante winkelverkoop werd onterecht als methode onbekend meegeteld; die wordt nu als kasontvangst getoond, met behoud van het totale ontvangen bedrag. Een ontbrekende oude verkoopdatum blijft onbekend.
- **Gebruikelijke teamroosters.** Directe inrichting per medewerkerskaart, met weekdagen, tijden en bron. Het fictieve voorbeeld vult alleen het formulier; opslaan is expliciet. Dagafwijkingen gaan vóór het weekrooster. Een bekende niet-werkdag toont nul capaciteit; ontbrekende inrichting toont onbekend. Pauzes, afwezigheid, gekoppelde reistijd en open/afgeronde afspraakvakken worden meegenomen. Afgeronde bezoeken zijn aanklikbaar in de daghistorie en hun tijdvakken worden niet opnieuw als vrij aangeboden.
- **Materiaal- en winkelroutes bewezen.** Vrije/gereserveerde voorraad, vrijgeven, verbruik, deelontvangst, vervolgbezoek, factuur, winkelretour en fictieve terugbetaling zijn via de interface getest. Vaste prijs met afwijkende uren en materiaal blijft de afgesproken prijs. Reeds aanwezige ontvangstbewijzen en revisies blijven dubbele mutaties blokkeren.
- **Eerlijke boekhoudgrens.** Financieel afgehandeld en boekhoudkundig verwerkt blijven afzonderlijk. Status, verantwoordelijke Administratie en bewijsreferentie zijn zichtbaar. Downloaden bevestigt niets; een afstemmingsfout heeft een directe route naar het boekhoudonderdeel.

## Browseracceptatie

Chromium en Playwright, afzonderlijke testkopie van uitsluitend fictieve gegevens op Server5. Alle muterende handelingen via zichtbare gebruikersschermen; API-GETs alleen voor controle. De eindronde start opnieuw uit de oorspronkelijke testfixture via run-browser-suite.py. Geen muterende acceptatietest op live dossiers.

| Gevraagde controle | Resultaat | Bewijs |
|---|---|---|
| 1. Terugboeken, opnieuw registreren en afsluiten | **Geslaagd** — €20 + €52,60 op €72,60; €20 teruggeboekt, correct opnieuw betaald, nulsaldo en afsluiting. Oorspronkelijke registratie bewaard. | browser-operations-results.json; compact-afgesloten-dossier.png |
| 2. Actuele waarschuwing verdwijnt na herstel | **Geslaagd** — W106 heeft in de fixture één onvolledige actieve betaling van €101,25 en één onvolledige teruggeboekte betaling. Aanvullen met bron verandert geen bedrag/afsluiting, actieve telling wordt nul, historische onvolledigheid blijft zichtbaar. | waarschuwing-afgehandeld.png; operations-results.json |
| 3. Dashboardbedrag doorklikbaar | **Geslaagd** — onbekende-methodebedrag is gelijk aan de som van de gefilterde actieve registraties; rechtstreeks naar de betreffende invoer. Ook oude factuur F101 en een betaling in een factuurarchief getest. | browser-operations-results.json; browser-extra-results.json; browser-archive-results.json |
| 4. Bekende/onbekende planning | **Geslaagd** — Noor en Lina aanvankelijk onbekend, expliciete fictieve roosters opgeslagen, gebruikelijke weekdag en niet-werkdag onderscheiden, dagafwijking 10–16, pauze, afwezigheid en gekoppelde reis ingevoerd. Lina houdt in het controlescenario exact 180 minuten over. Afgeronde bezoeken blijven zichtbaar en tellen als bezette tijd. | planning-onbekend.png; planning-ingesteld-en-historie.png; dagplanning-met-afwijkingen.png |
| 5a. Materiaal uit voorraad | **Geslaagd** — voorraad 5, reservering 2 → vrij 3, vrijgeven → vrij 5, verbruik 1 → voorraad 4. Factuur €60 arbeid + €10 materiaal = €70 excl. / €84,70 incl. | materiaal-naar-factuur.png |
| 5b. Inkoop en vervolg | **Geslaagd** — bestelling 2, ontvangst 1+1, diagnose 0,5 uur en vervolg 1 uur, één onderdeel van €15 verbruikt; factuur €105 excl. / €127,05 incl. Eigenaar ziet de leveringsblokkade. | inkoop-en-vervolg.png |
| 5c. Winkelretour en terugbetaling | **Geslaagd** — voorraad 3 → verkoop 2 → 1; twee retouren van 1 → voorraad 3. Verkoop en refunds beide samen €24,22 incl.; btw €4,20. Netto-ontvangst keert terug naar het beginbedrag. | winkelretour-voorraad-en-geld.png |
| 6. Herladen en dubbelklikken | **Geslaagd** — afsluiting blijft na herladen staan. Dubbele klik op betaling, materiaalverbruik en winkelretour geeft geen dubbele verwerking. Backend test ook identieke aanvraagreplay en herhaalde vrijgave/retour. | browser-operations-results.json; operations-results.json; financial-results.json |
| Vaste offerteprijs behouden | **Geslaagd** — €100 excl. inclusief materiaal, 2 werkelijke uren en €25 geregistreerd materiaal; concept blijft één regel van €100 excl. / €121 incl., zonder uurtariefinvoer. | browser-extra-results.json |
| Mobiele bediening | **Geslaagd** — 390×844, precies één primaire dossieractie zichtbaar binnen de viewport, geen horizontale paginaoverflow. | visual-results.json; compact-mobiel-viewport.png |

De oude uitgebreide financiële regressietests slagen eveneens: financiële berekeningen, credits/refunds, cumulatieve btw, vervangende facturen, broncorrecties, onbekende waarden, revisieconflicten, verloren antwoord, tijdelijke opslagfout en gecontroleerd herstel. De bestaande browsertest voor twee afzonderlijke vensters uit ronde 2 is **niet opnieuw uitgevoerd** in deze ronde; revisiebescherming is automatisch getest. Geen nieuwe fysieke telefoon-/spraakacceptatie geclaimd.

## Export en gegevenscontrole

export-check.py / export-results.json controleren **39 gekoppelde regels** in de uiteindelijke fictieve testadministratie. IDs zijn uniek, ouders aanwezig, credits/refunds/betalingen sluiten per factuur/verkoop aan en omzet/netto-ontvangsten zijn gelijk aan het dashboard. Ontbrekende gegevens en mappings blijven expliciet. Download wijzigt geen toestand. export-sample.csv is het exacte controlevoorbeeld met CSV-standaard CRLF.

**Externe importvalidatie: niet getest/openstaand.** Geen boekhoudpakket of koppeling verzonnen. De voorbereiding en mappings blijven beschreven in README; een handmatig bevestigde status vereist een afzonderlijke bewijsreferentie.

## Live oplevering en behoud

Server4 `/home/mau/server4-mobile-demo`: gewijzigd business.py, workflow.py, data.py, improvements.py, static/app.js, static/style.css en README.md. app.py, recovery.py en static/index.html ongewijzigd meegeverifieerd. Geen nieuwe permanente service of software-installatie; bestaande userdienst herstart en browserhulpmiddelen hergebruikt.

deployment-results.json: health plus zes routes HTTP200, assets gelijk aan bron, broncontrole tegen gelijktijdige wijzigingen en **workflow vóór/na byte-identiek**, SHA256 `9552e463e574b4f55a2687e4fc24035c963a1ae766bd4eb6780dedfbf6d10c38`. W106, W109, alle overige dossiers, histories, betalingen, voorraden en bestaande dagroosters behouden. Geen automatische live inrichting van Noor/Lina; de eigenaar kan die bewust invoeren of het expliciet fictieve voorbeeld kiezen.

Live read-only browsercontrole: live-browser-results.json; screenshots live-dashboard.png, live-W106.png, live-W109.png en live-mobiel-viewport.png. Mobiele primaire actie en gebrek aan paginaoverflow gecontroleerd. Tijdelijke SSH-loopbackforward bewijst lokale HTTP via bestaande private SSH, geen nieuwe private HTTPS- of telefoonroute. Tijdelijke testserver en forward worden na acceptatie gestopt.

## Backup en rollback

Server4 backup vóór mutatie: `backups/demo_conf_operations_20261026_003/`. Laatste volledige bron/data/manifest-snapshot staat onder new_snapshot in deployment-results.json. Geen authbestanden opgenomen. Nieuwe roostergegevens en betaalhistorie staan in dezelfde workflow.json en vallen automatisch mee in de bestaande recovery.py; monitoring en backups zijn niet vervangen.

Rollback: controleer latere wijzigingen, stop bestaande demo-userdienst, herstel uitsluitend de gewijzigde bronbestanden met hun relatieve paden uit de taakbackup, start de dienst en controleer health, bedragen en dossiers. **Geen datarestore nodig voor bronrollback.** Zet workflow-reference.json niet blind over nieuwere gegevens terug. Voor bewust gegevensherstel: README/recovery.py met manifestcontrole en before-restore-backup. Geen live restore uitgevoerd. Original/ bewaart de bron vóór deze ronde ook lokaal.

## Henk-oordeel en beperkingen

**Praktijkproef: ja, gecontroleerd met fictieve gegevens.** Minder zoekwerk door één primaire actie, directe betaalwaarschuwingen, leesbare betalingsnamen en roosterinrichting op de medewerkerskaart. Monteur en administratie gebruiken hetzelfde materiaal/verbruik en dezelfde bedragen. Financiële correcties behouden hun oorspronkelijke registraties.

Nog omslachtig: bewijsstukken beoordelen en boekhoudmapping blijven handwerk; uitgebreide uitzonderingen staan onder uitklaponderdelen. Capaciteit betekent ingevoerde rooster-/afspraakvakken, geen live tijdregistratie of automatisch bekende reistijd. Bezoeken zonder vastgelegde datum/tijd worden niet op een verzonnen dag geplaatst. Onbekende inrichting blijft terecht onbekend.

Aanschaf/productie vereist nog echte accounts/rechten, gevalideerde externe boekhoudimport, gewenste bank/mail/leverancierskoppelingen, stamgegevens/kostprijsadministratie en operationele externe backup. Eén JSON-opslag/schrijfproces blijft de demogrens. Rollen zijn presentatie. Externe acties zijn lokale fictieve registraties. Deze beperkingen zijn gescheiden van de in deze ronde herstelde en bewezen functies; geen algemene bugvrijheid geclaimd.

## Taakafsluiting

Succeeded. Current Projects 4 vóór → 6 tijdens → 4 na; eigen taak en uitvoeringsblad met bewijs gesnoeid, bestaande telefoonblokkade behouden. during-validation.json/final-validation.json: consistent=true, bronhash=publicatiehash, project_invariants_valid=true, iedere done-node een blad. CLI-taak zonder brokerrecord; geen brokerresultaat verzonnen. Volgende stap: demo herladen en de directe betaal-/roosteracties met fictieve gegevens uitproberen. Geen externe publicatie.
