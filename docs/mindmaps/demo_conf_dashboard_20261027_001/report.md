# Demo-conf dashboard — 27 oktober 2026

Uitgevoerd vanaf hostname server5 op expliciet verzoek om de Server4-demo aan te passen volgens /home/mau/demo-conf.md (kopie: requirements.md). Bestaande SSH-route gebruikt; Server4 heeft geen Git-repository en geen toepasselijke AGENTS.md in /home/mau of de appmap. Server5-Gitstatus vóór uitvoering gecontroleerd; bestaand werk behouden.

## Resultaat

- Aandachtspunten staan vóór de uitgebreide planning: klant, probleem, verantwoordelijke, deadline of expliciet onbekend, relevant open factuurbedrag en één duidelijke vervolgactie. Spoed/onderdelen/financiële opvolging worden geprioriteerd. Dubbele werkacties worden samengevoegd; afzonderlijke vervallen facturen blijven afzonderlijk herkenbaar. Uitgebreide blokkade-informatie is uitklapbaar.
- Eén onderdeel **Betaalgegevens controleren** telt unieke actieve betalingen. Filters: ontbrekende methode, referentie, bronbevestiging en datum. Elke rij bevat klant, factuurnummer, bedrag, datum, methode en ontbrekende gegevens; de knop opent precies die betaling, ook bij een oude factuur. Een betaling kan in meerdere filters vallen. Teruggeboekte betalingen blijven historie en tellen niet als actieve waarschuwing. Een ontbrekende bronbevestiging wordt ook herkend als datum/methode/referentie al bestaan.
- Bovenaan staat **Demodag: maandag 26 oktober 2026**. Automatische bedrijfsdatums en factuuropvolging gebruiken dezelfde vaste dag als planning en debiteurenfilters. Werkelijke UTC-auditstempels en bestaande historische feiten blijven behouden.
- Planning toont werktijden, eerstvolgende afspraak en vrije capaciteit in uren/minuten. Totale vrije dagcapaciteit en resterende capaciteit vanaf een zelf gekozen, zichtbaar simulatietijdstip zijn afzonderlijk. Standaard 09:00; geen gebruik van de echte klok. Onbekende capaciteit wordt niet als vrije tijd gepresenteerd. Volledige tijdlijn en afgeronde bezoeken zijn uitklapbaar; afgeronde bezoektijd blijft bezet. Roosters en dagafwijkingen blijven instelbaar.
- Lege open-werktoestand verklaart waar factureerbare dossiers en gefactureerde dossiers staan. Primaire aandachtspuntknoppen hebben menselijke namen. Waarschuwingen hebben tekst én een afwijkende rand. Geen horizontale paginaoverflow of afgebroken knoppen op 1366, 760 en 390 pixels breed.
- Aanvullend hersteld: een gereedgemelde opdracht met onderdeelhistorie kon uit de aandachtspunten voor facturatie verdwijnen. Nu blijft zij zichtbaar tot de volgende administratieve overgang.

## Tests

Alle muterende proeven op een afzonderlijke fictieve kopie op Server5. Productie uitsluitend gelezen voor eindacceptatie. Geen echte berichten, bestellingen, betalingen of boekingen verstuurd.

| Controle | Resultaat | Bewijs |
|---|---|---|
| Opdracht gereedmelden → dashboard en dossier factureerbaar | Geslaagd | browser-operations-results.json; finish-helper controleert beide leesmodellen |
| Betaling registreren/terugboeken/opnieuw afsluiten | Geslaagd | browser-operations-results.json; unit-results.json |
| Ontbrekende betaalgegevens aanvullen → unieke waarschuwing verdwijnt zonder bedragwijziging | Geslaagd | browser-operations-results.json; operations-tests.py |
| Onderdeel deels/volledig ontvangen → vervolgafspraak, verbruik en factuur | Geslaagd | browser-operations-results.json; inkoop-en-vervolg.png |
| Rooster/afspraak/pauze/afwezigheid/reistijd wijzigen | Geslaagd | browser-extra-results.json; operations-tests.py; dashboard-results.json |
| Winkelretour → voorraad en fictieve geldmutatie sluiten aan | Geslaagd | browser-operations-results.json; winkelretour-voorraad-en-geld.png |
| Oude factuur/archiefbetaling direct bereikbaar, vaste prijs behouden | Geslaagd | browser-extra-results.json; browser-archive-results.json |
| Dashboard, betalingen, credits, debiteuren en voorraad consistent | Geslaagd | vijf geïsoleerde Python-suites in unit-results.json; 39 exportregels afgestemd in export-results.json |
| Simulatietijd en overlappende bezetblokken; onbekende capaciteit | Geslaagd | dashboard-results.json, vijf tijdstippen; live/visual-results.json |
| Laptop/smal browserpaneel en primaire knoppen | Geslaagd | visual-results.json en live/visual-results.json; nul browserfouten |
| Backup/manifestcontrole en geïsoleerd herstel | Geslaagd | unit-results.json; final-backup.json |
| Fysieke telefoon, spraak, private HTTPS naar Server4 | Niet getest in deze opdracht | Bestaande afzonderlijke telefoonblokkade behouden |
| Externe boekhoudimport of echte verwerking | Niet getest | Blijft fictieve lokale administratie; exports zijn geen boekingen |

Tijdens ontwikkeling gevonden fouten en verouderde testselectoren zijn hersteld; de genoemde eindresultaten zijn de geslaagde eindronde. De testfixture maakt Noor/Lina bewust onbekend voor de onbekend→ingericht-proef; live roosters zijn niet gewijzigd.

## Publicatie en behoud

Gewijzigde live bron: business.py, data.py, improvements.py, static/app.js, static/index.html, static/style.css en README.md onder /home/mau/server4-mobile-demo. De overige applicatiebronnen bleven gelijk. Bestaande userdienst één keer herstart; laatste CSS-specificiteitscorrectie rechtstreeks als statisch bestand gepubliceerd. Geen nieuwe permanente service, installatie, netwerk-, SSH-, authenticatie- of firewallwijziging.

Live /health en zes routes HTTP200. Assets gecontroleerd tegen de kandidaatbron. Workflow vóór/na byte-identiek: SHA256 `934222da907ff39c5ef826a66fd0482a59440c80ef480a426e522856a0bb55a3`. Dit behoud omvat alle dossiers, betalingen, histories, voorraden en bestaande roosters. Zie deployment-results.json, css-publication.json en live-final-results.json. De laatste backup met de definitieve CSS staat in final-backup.json; monitoring en bestaande recovery.py blijven behouden.

Live screenshots: live/dashboard-1366.png, live/betalingscontrole-1366.png, live/planning-1366.png; ook dezelfde drie op 760 en 390 pixels. Tijdelijke loopback-SSH-forward bewijst private SSH + lokale HTTP, geen nieuwe private HTTPS-/telefoonroute.

## Rollback en beperkingen

Server4 bronbackup vóór wijzigingen: `/home/mau/server4-mobile-demo/backups/demo_conf_dashboard_20261027_001/`. Controleer latere wijzigingen; stop alleen de demo-userdienst, herstel de zeven gewijzigde bronbestanden met relatieve paden, start dezelfde dienst en controleer health/dossiers/bedragen. **Geen workflow-restore nodig voor bronrollback.** Gebruik workflow-reference.json niet blind over nieuwe historie. original/ bewaart ook de oorspronkelijke bronnen op Server5.

Capaciteit blijft gebaseerd op ingevoerde roosters en afspraakvakken, inclusief afgeronde bezoeken; ontbrekende gegevens blijven onbekend. Het gekozen simulatietijdstip geldt zolang deze pagina openstaat en begint na herladen weer op 09:00. De vaste dag wordt bewust niet naar de hostdatum verzet. Eén JSON-schrijfproces, presentatie-rollen en ontbrekende echte accounts/koppelingen blijven demobeperkingen. Geen productiegeschiktheid of onbeheerde Notion-synchronisatie geclaimd.

## Taakafsluiting

Succeeded. Current Projects: 4 nodes vóór → 6 tijdens → 4 na. Eigen taaknode en stap met bewijs gesnoeid; bestaande telefoonblokkade behouden. Eindvalidator: consistent=true, bronhash=publicatiehash, project_invariants_valid=true, iedere done-node een blad. CLI-opdracht zonder brokerrecord; alleen kaartstatus bijgewerkt. Tijdelijke testserver en SSH-forward gestopt.

Notion-snapshot gepubliceerd en teruggelezen: https://app.notion.com/p/406c7b0333768134b3f1d5b13b266f7f ; centraal gedeeld werklog bijgewerkt. Geen permanente synchronisatie ingericht. Volgende stap: bestaande demo in browser herladen en het dashboard gebruiken; afzonderlijke telefoonblokkade blijft buiten deze opdracht.
