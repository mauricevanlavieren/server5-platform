# Server4 verkoopdemo — 27 oktober 2026, ronde 3

**Verbeteringen uitgevoerd en live gecontroleerd.** Nieuwste opdracht /home/mau/demo-conf.md bewaard als requirements.md. Taak demo_conf_sales_20261027_003. Host server5 en bestaande ongecommitte wijzigingen vooraf gecontroleerd; bestaande Server4-demo via de geautoriseerde SSH-route bijgewerkt. Geen nieuwe dashboardapp, installatie, publieke interface of externe publicatie. Bestaande histories en gebruikersgegevens behouden.

## Oordeel vanuit Henk

| Onderdeel | Oordeel | Grens |
|---|---|---|
| Verkoopdemo | **Gereed voor fictieve demonstraties** | Alle drie klantreizen aantoonbaar uitgevoerd via bestaande schermen. Geen bekende kritieke fout in deze geteste demoscope verborgen. Dit is geen verkoopcontract of productiecertificering. |
| Praktijkproef | **Begeleide fictieve praktijkproef gereed** | Een proef met echte klant-/bedrijfsgegevens wacht op accounts/rechten, privacy/beveiligingsafspraken, inrichting, beheer en toestemming. Geen echte transacties getest. |
| Productie | **Niet gereed** | Productieaccounts, integraties/import, externe backup, operationele en commerciële afspraken ontbreken. |

Een ondernemer kan de routes en beperkingen lezen onder **Rondleiding** en **Praktijkproef en aanschaf**. Het compacte dashboard blijft de gewone werkplek. Rondleiding maakt op expliciete bevestiging nieuwe fictieve dossiers en vier exemplaren van een uniek oefenartikel. Een nieuwe ronde bewaart alle eerdere rondes, dossiers, voorraden en histories; niets wordt gereset of gewist. Op live zijn nog geen oefenrondes namens de gebruiker aangemaakt. De knop zet ze veilig klaar wanneer de gebruiker daarvoor kiest.

## Eerst herstelde praktijkfouten

- **Materiaal vrijgeven:** zichtbare formulieren met gekozen hoeveelheid en reden; gedeeltelijke vrijgave laat de rest gereserveerd en verandert de fysieke voorraad niet. Voorraad/vrij beschikbaar en reserveringen worden direct herberekend. De knop staat ook na gereedmelden bij de actieve materiaalbediening, niet verstopt tussen historische uitvoeringsgegevens.
- **Materiaalretour:** gedeeltelijke retour ondersteunt voorraad en herleidbare conceptcorrectie. Oorspronkelijke hoeveelheid, resterend verbruik en transitiehistorie blijven bewaard. Een definitieve factuur blijft ongewijzigd; retour vereist een voldoende creditreferentie. Creditallocatie wordt cumulatief bewaakt. De factuurcontrole houdt rekening met het gecrediteerde retouraantal. Te veel vrijgeven/retourneren, onjuiste status, dubbele aanvraag en ontoereikende credit zijn getest.
- **Retourhistorie:** artikel, aantal, datum, reden, bedrag, methode en oorspronkelijke verkoop staan leesbaar in beeld; geen [object Object]. Ook geneste dossier-/afrekenhistorie krijgt leesbare labels in plaats van ruwe JSON.
- **Opslagfeedback:** één zichtbare melding voor de nieuwste handeling, met succes of concrete fout; een volgende opslag verwijdert oude foutfeedback. Netwerkfouten behouden invoer. Aanvraagherhaling na een verloren antwoord is beschermd tegen dubbele verwerking.
- **Factuurdatums:** nieuwe definitieve facturen krijgen de vaste demodatum. Ontbrekende historische datums blijven onbekend tot gecontroleerde aanvulling met bron en historie. Een bekende definitieve datum kan niet stilzwijgend worden overschreven. Aanvulling staat als invoice_date_metadata in de export. Historische facturen uit zoekresultaten openen nu direct de volledige factuurbediening; bij een factuurkaart opent de actie precies de betreffende factuur.
- **Presentatie:** open bestelrestant expliciet zichtbaar; artikelzoekfunctie in de bestaande voorraad-/winkelwerkplek; rondekeuze opent echte dossiers en verkoopformulieren. Aanschafpagina werkt op laptop en smaller paneel, met toetsenbordfocus. De oude illustratieve aanname van 60 seconden is verwijderd; alleen concrete bronvelden/overdrachten worden geteld, geen gemeten of verzonnen tijdsbesparing.

## Bestaande praktijkproef behouden

De live toestand vóór/na publicatie is **byte-identiek**, SHA256 `ce2f1e62aade2aa6f00ae3a07e74b6c859273b1d061044b8803ce11be95488a2`.

- I2: 4 artikelen, 4 ontvangen in de bestaande deelontvangsthistorie.
- B2: 2 × €10 excl. → €24,20 ontvangen; 1 retour → €12,10 terugbetaald en 1 op voorraad terug.
- W113: 2 artikelen plus 1 uur → concept €80 excl. / €96,80 incl. btw.
- Dashboard netto ontvangen: **€772,90**, behouden. Alle andere dossiers, histories, roosters, betalingen en voorraden eveneens behouden.

Zie live-reference.json, deployment-results.json en live-final-results.json. De nieuwe proefregistraties hieronder bestaan uitsluitend in de afzonderlijke Server5-testkopie.

## Drie volledige klantreizen — browserbewijs

Headless Chromium/Playwright op Server5 voor de bedrijfsroutes; mutaties uitsluitend via zichtbare gebruikersbediening, API-reads als afstemmingscontrole. Eindronde startte uit een kopie van de live administratie; Noor/Lina-roosters werden alleen in die testkopie bewust onbekend gemaakt voor de inrichtingstest. Geen muterende acceptatietest op live dossiers.

| Reis | Resultaat en bewijs |
|---|---|
| A · Monteur | **Geslaagd.** Nieuw fictief dossier W119: offerte €100, klantakkoord, vaste prijsafspraak, planning, 2 artikelen reserveren/verbruiken, 1 uur uitvoeren, één factuurregel van €100 excl. / €121 incl., fictief verzonden, €121 bankbetaling en administratief afgesloten. Geen dubbel materiaal; offertebedrag gaat mee. Screenshot reis-A-afgesloten.png. |
| B · Ontbrekend onderdeel | **Geslaagd.** W120: diagnose en akkoord/planning, onderdeelbehoefte, inkoop 4, fictieve bestelling, ontvangst 2+2 met zichtbaar restant 2→0, afzonderlijk vervolgbezoek, intern afgehandelde klantopvolging zonder verzending, verbruik 2, diagnose 0,5 + vervolg 1 uur. Factuur €110 excl. / €133,10 incl., fictief verzonden en als open debiteur zichtbaar. Screenshots reis-B-open-bestelrestant.png en reis-B-gefactureerd.png. |
| C · Winkelbalie | **Geslaagd.** Artikel zoeken, vrije voorraad controleren, verkoop B4 van 2 × €10 excl. → €24,20 fictief contant ontvangen. Eén retour → €12,10 terugbetaald, voorraad van 0 naar 1. Verkoop, retourhistorie, voorraad en netto ontvangsten sluiten aan. Screenshots reis-C-retourkaart.png en reis-C-retourhistorie.png. |
| Nieuwe oefenronde | **Geslaagd.** D2 voegt nieuwe dossiers en een nieuw artikel toe; D1 en het afgesloten dossier blijven ongewijzigd. journey-results.json; sales-results.json. |

Rondleiding toont wie aan zet is en de volgende dossierstap. Bij vaste prijs gaat één afgesproken offertebedrag mee; bij nacalculatie worden het urentotaal en gekoppelde materiaalverbruiken uit de bron overgenomen. Verkoopprijsbronnen en goedkeuringen blijven bewuste controlehandelingen. Deze aantallen zijn controleerbaar in dossier/factuur; geen claim over uitgespaarde minuten.

## Financiële, voorraad- en correctietests

| Controle | Eindstatus | Bewijs |
|---|---|---|
| Nacalculatie versus vaste prijs | **Geslaagd** | Browserreis A, browser-extra-results.json, finance-extra-results.json. Vast €100 blijft €100; expliciete nacalculatie 1,5 uur × €60 = €90 na controle van de offerteafwijking. |
| Afzonderlijk meerwerk | **Geslaagd** | finance-extra-results.json: ontbrekend apart akkoord geweigerd; €100 offerte + €20 goedgekeurd meerwerk = €120 excl. / €145,20 incl.; definitieve afspraak niet overschreven. |
| Materiaal zonder dubbel factureren | **Geslaagd** | Browserroutes A/B en financieel bron-/regelcontrole; gekoppelde reserveringsregels. |
| Btw/afronding, deelbetaling, terugboeking, credits, refunds, saldo/tegoed | **Geslaagd** | financial-tests.py/status-tests.py in unit-results.json; browser-operations-results.json; cumulatieve credit-btw en gedeeltelijke winkelretour sluiten exact. |
| Gedeeltelijke vrijgave en materiaalretour | **Geslaagd** | fixes-browser-results.json; sales-results.json; gedeeltelijke-materiaalretour.png. Te grote aantallen worden geweigerd zonder mutatie. |
| Geen dubbele verwerking | **Geslaagd** | Dubbelklikken, revisies en aanvraagreplay getest. Verloren antwoord na daadwerkelijke opslag opnieuw aangeboden: één opgeslagen actie. |
| Omzet versus netto ontvangen | **Geslaagd** | 211 afstemmingscheckpoints in step-reconciliation.jsonl; dossier, voorraad, debiteuren en getekende export vergeleken. |
| Exportkoppeling en totalen | **Geslaagd** | export-results.json: 51 unieke, gekoppelde regels; 16 ouderfacturen/-verkopen. Testadministratie: €1.250,00 omzet excl. en €906,00 netto ontvangen incl.; dit zijn de gewijzigde fictieve testtotalen, niet de behouden live €772,90. |
| Externe import in boekhoudpakket | **Niet getest / open** | Geen geautoriseerde testomgeving of bestaande externe koppeling beschikbaar in deze demo. Geen succesvolle import geclaimd. |

Zeven geïsoleerde berekenings-/status-/hersteltestsuites slagen in unit-results.json. Aanvullend herstel van de volledige bron plus eindadministratie: recovery-full-results.json. De definitieve sequentiële browserronde staat in acceptance-results.json; ontwikkelingstests met gevonden fouten zijn hersteld en vervangen door deze geslaagde eindronde.

## Samenwerken, fouten en herstel

**Geslaagd in twee echte afzonderlijke Chromium-vensters**, headed onder Xvfb :97 op Server5; verschillende Browser.windowId-waarden vastgelegd in window-identities.json. Dit is een virtueel beeldscherm, geen fysieke telefoon of twee echte bedrijfsgebruikersaccounts.

- Automatische synchronisatie van een schone sessie en behoud na herladen.
- Gelijktijdige invoer: de oude versie wordt geweigerd; eigen onopgeslagen tekst blijft staan; actuele gegevens expliciet ophalen herstelt het conflict.
- Verloren antwoord: de browserrequest wordt pas na serververwerking afgebroken; opnieuw opslaan geeft één actie, geen duplicaat.
- Browser-opslagfout: expliciete gesimuleerde HTTP500; invoer blijft, fout is zichtbaar, opnieuw opslaan herstelt en verwijdert oude feedback. Daarnaast echte foutinjectie in de geïsoleerde opslagcode getest in status-tests.py.
- Geen verborgen verlies van oorspronkelijke registraties; snapshots, historie en bronbedragen blijven aanwezig.

Zie collaboration-results.json, samenwerken-conflict-eerste-venster.png, samenwerken-tweede-venster.png en opslag-herstel-feedback.png.

**Volledig geïsoleerd herstel geslaagd:** alle bron-/statehashes, voor-herstelbackup met nieuwere markerdata, echte herstelde HTTP-app met dashboard/workflow/export/aanschafpagina, 250 historische acties en oefenrondes gecontroleerd. Gemanipuleerde backup geweigerd vóór schrijven. Veertien bestanden in de testbackup (geen tegelconfig nodig); vijftien in de live snapshot inclusief bestaande tiles.json. Geen live restore uitgevoerd.

## Boekhouding en aanschaf

De CSV vermeldt oorspronkelijke IDs, parent_payment, facturen, credits, ontvangsten, terugboekingen, refunds, metadatahistorie, bronhash en ontbrekende velden. Netto ontvangen = som cashflow_effect_cents; net_received_cents alleen op invoice/sale-ouderregels sommeren. Credits veranderen omzet/saldo, niet zonder afzonderlijke refund het geld. UNKNOWN blijft ontbrekende informatie.

Voor een echte import ontbreken onder meer bevestigde debiteurmapping, dagboeken, grootboek-/btw-codes, formaat/tekenconventie van het doelpakket en een testimport met teruggelezen bewijs. Downloaden wijzigt geen verwerkingsstatus. Een eigen verklaring met bewijsreferentie is uitdrukkelijk geen onafhankelijk gevalideerde externe verwerking.

De pagina /praktijkproef bevat doelgroep, inbegrepen en uitgesloten demofuncties, inrichting/import, koppelingen, begeleiding, ondersteuning/verantwoordelijkheden, opslag/backup/uitvoer en een afgebakend proefvoorstel met meetbare criteria. Prijs, licentie, serviceafspraken, beveiligingsgaranties en contractvoorwaarden zijn **Nog vast te stellen**. Afzonderlijke beslislijst: aankoopbeslissingen.md.

Resterende aankoopbelemmeringen, op belang: (1) productieaccounts/rechten/privacy/beveiliging; (2) doelkoppelingen en gevalideerde import/migratie; (3) externe backup, beheer en hersteldoelen; (4) prijs, contract, ondersteuning en begeleiding. Balieverkoop is fictieve kasregistratie, geen echte pin-/bank-/kassakoppeling. Eén JSON-schrijfproces en presentatie-rollen blijven demogrenzen.

## Publicatie, backup en rollback

Live health en zeven routes HTTP200, waaronder /praktijkproef; assets gelijk aan de geteste bron. Live browser op 1366×768, 760 en 390 pixels: belangrijkste aandachtspunt met kerncijfers in laptopbeeld, geen horizontale paginaoverflow, zichtbare toetsenbordfocus en geen ruwe objecttekst. Zie live/visual-results.json en live/rondleiding-1366.png, live/aanschaf-390.png. De gewone bedrijfswerkplek blijft zelfstandig bruikbaar.

Bestaande userdienst eenmaal herstart. Gewijzigd: app.py, business.py, workflow.py, data.py, improvements.py, recovery.py, static/app.js, static/style.css, static/index.html, README.md. Nieuw: sales.py en static/praktijkproef.html. Geen netwerk/SSH/firewall/authenticatie/reboot/installatie, echte berichten/bestellingen/betalingen of externe boekhouding. Monitoring en backups behouden.

Herstelpunt: `/home/mau/server4-mobile-demo/backups/demo_conf_sales_20261027_003/`. Definitieve bron/data-snapshot: `/home/mau/server4-mobile-demo/backups/snapshot-20261027T075741589077Z/`; alle 15 bestanden en manifesthashes gecontroleerd, bron gelijk aan live. Nieuwe datum-/materiaal-/oefenrondehistorie valt onder bestaande workflow.json-backup. Bewijs: live-final-results.json.

Rollback: beoordeel latere wijzigingen; stop alleen server4-mobile-demo.service, herstel de tien gewijzigde bestaande bronbestanden uit het herstelpunt en verwijder uitsluitend de twee hierboven nieuw genoemde bronbestanden als die niet later zijn gewijzigd. Start dezelfde dienst en controleer health, dossiers, bedragen en voorraad. **Geen workflow-restore voor bronrollback.** Zet de workflow-reference.json nooit blind over nieuwere gebruikershistorie. Original/ bewaart de eerdere bronnen ook lokaal op Server5.

De tijdelijke testserver, SSH-loopbackforward en eigen Xvfb-testdisplay worden na acceptatie gestopt. Private SSH + lokale HTTP bewijzen geen nieuwe telefoon-/spraak- of private HTTPS-route. Fysieke telefoon, echte bedrijfsaccounts, externe import en productieacceptatie zijn niet getest.

**Geen externe publicatie:** de nieuwste demo-conf.md verbiedt dit expliciet. Daarom deze ronde geen Notion-snapshot/werklogpublicatie; lokale Markdown, Git en de bestaande lokale Current Projects-kaart bevatten de voortgang en het bewijs. Dit is een bewuste toepassing van de actuele eigenaaropdracht op de oudere standaarddocumentatie-instructie.

## Taakafsluiting

Succeeded. Current Projects 4 vóór → 6 tijdens → 4 na. Eigen taak en actieve uitvoeringsstap met bewijs gesnoeid; bestaande telefoonblokkade behouden. Eindcontrole: consistent=true, bronhash=publicatiehash, project_invariants_valid=true, iedere done-node een blad. CLI-opdracht zonder brokerrecord; alleen kaartstatus bijgewerkt. Tijdelijke testserver, private loopbackforward en eigen Xvfb-testdisplay gestopt. Geen Notion-/andere externe publicatie volgens de actuele opdracht. Volgende stap: demo herladen, Rondleiding openen en bewust nieuwe oefenroutes klaarzetten; aankoopbeslissingen apart vaststellen vóór echte bedrijfsproef/productie.
