# Server4 proefvoorstel en levering — 27 oktober 2026, ronde 6

**Onafhankelijk uitvoerbaar werk afgerond; aangepaste fictieve demo actief op Server4.** Nieuwe ingang: **Proefvoorstel en acceptatie** (/proefvoorstel). Geen nieuwe dashboardfuncties. De knop Toegang demo blijft werken. Concrete scope, drie deelnemersroutes, acceptatiecriteria, zakelijke beslisvelden en eerlijke boekhoud-/backupgrenzen toegevoegd. Git/hostname vooraf gecontroleerd; bestaande ongecommitte Server5-wijzigingen behouden. Server4 heeft geen eigen Git-repository; geteste bron, diff en bewijs staan bij deze taak.

Taak demo_conf_delivery_20261027_006. Bron requirements.md plus nadere eigenaarinstructies in owner-steering.md en de chat. Nieuwe toestemming voor Server4 is niet opnieuw gevraagd: dit is dezelfde eerder expliciet geautoriseerde demo-opdracht. Uitvoering uitsluitend op Server5 en via bestaande geverifieerde SSH op Server4. Geen router/andere hosts, publieke route, SSH-/Codex-authwijziging, rootwijziging of reboot. Geen externe SaaS/boekhoudomgeving gekozen of benaderd. Geen echte berichten/bestellingen/betalingen.

## Wat nu werkt

- **Concreet proefvoorstel:** voorbereiding met fictieve gegevens, eigenaar/begeleider/deelnemers/periode/kostenafspraak, drie bestaande routes, controles, herstel-/boekhoudproef en evaluatie. Geen duur, prijs of supportcontract aangenomen.
- **Herleidbare keuzes:** eigenaar kan periode, prijzen/inbegrepen/uitgesloten werk, migratie/training, ondersteuning, hosting/backup, looptijd/opzegging/uitvoer en boekhoudkeuzes met bron/akkoordreferentie opslaan. Lege velden blijven Nog vast te stellen. Versies en actor/tijd blijven bewaard. Invoer is geen onafhankelijke leveranciersinstemming.
- **Winkelrol:** eigen beperkte werkplek voor vrije voorraad, fictieve contante verkoop en deelretour/terugbetaling. Geen toegang tot klantdossiers, debiteuren, bedrijfsdashboard, export, tarieven of gebruikersbeheer. Persoonlijke winkelaccounts via bestaand eigenaarbeheer; andere rollen behouden.
- **Medewerkersacceptatie:** monteur, winkelmedewerker en administrateur kunnen eigen route als geslaagd/mislukt/geblokkeerd met beoordeelde stappen en concrete bevindingen vastleggen. Demo-/eigenaarwaarnemingen tellen niet als zelfstandige acceptatie door de drie rollen. Registraties blijven eigen verklaringen, geen onafhankelijke certificering.
- **Praktische fout hersteld:** het bestaande administratieformulier stuurde bij Geen materiaal lege/0-materiaalvelden; de rechtencontrole weigerde daardoor een normale factuur. Lege ongebruikte velden zijn nu toegestaan, daadwerkelijke onbevoegde prijswijzigingen blijven geweigerd. De echte browseroverdracht monteur → administratie bewijst dit.
- **Pakketneutrale boekhouding:** data.accounting_snapshot() levert een read-only domeinmomentopname. accounting.py serialiseert die zonder database-, netwerk- of bedrijfsregelimports. Facturen, credits, betalingen, terugboekingen, refunds en winkelretouren behouden nummers, relaties, bronhashes, bedrijfsdatums/registratiestempels en centbedragen. Bestaande CSV-interface blijft compatibel; JSON-bronmomentopname is beschikbaar voor latere adapterbouw.
- **Zichtbaar boekhoudhandwerk:** bronproblemen, document-/regelsoorten en aantallen, ontbrekende datums/betaalbronnen, mappings, doelformaat, koppelen en teruglezen. Geen pakket gekozen of tijdwinst verzonnen.
- **Lokale backup/herstel:** actuele nieuwe bron/staat lokaal op Server4 opgeslagen en in aparte lokale app-/statemappen hersteld, met werkende herstelde app/demo-ingang en gelijke bedrijfstoestand/bedragen/export. Gegevens niet live teruggezet. Instelbaar niet-actief backupvoorbeeld en procedure voor een later expliciet gekozen bestemming voorbereid.

## Oordeel en open punten

| Gebruik | Oordeel | Grens |
|---|---|---|
| Verkoopdemo | Geschikt voor fictieve demonstratie | Gedeelde demotoegang is geen persoonlijke medewerkersidentificatie |
| Begeleide fictieve praktijkproef | Technisch bruikbaar met proefplan en rollen | Echte deelnemers moeten nog zelf accepteren; periode/kosten/begeleiding nog kiezen |
| Externe boekhoudkoppeling | **Niet gevalideerd** | Er is nog geen pakket of geautoriseerde testomgeving gekozen; blokkeert fictieve afwerking niet |
| Externe backup | **Nog niet ingericht en getest** | Geen door eigenaar gekozen/geautoriseerde bestemming in gebruik |
| Ondersteuning | **Nog vast te stellen** | Contactpersoon, contactgegevens, bereikbaarheid en responstijd niet ingevuld |
| Productie | Niet gereed | Zakelijke afspraken, echte medewerkersacceptatie, externe boekhoud-/herstelbewijzen en beheer/privacy ontbreken |

### Twee afzonderlijke beslissingen vóór echt bedrijfsgebruik

1. **Back-up:** kies een bestemming buiten Server4 en geef toestemming voor gebruik. Leg budget, verantwoordelijke, toegangsrechten, frequentie/retentie, encryptie/sleutelbewaring en hersteldoelen vast. Configureer en test daarna kopie én herstel vanaf die daadwerkelijke bestemming. backup-config.example.json is bewust niet actief; geen extern pad/account/dienst vooraf aangenomen. Een andere filesystem/mount is op zichzelf geen bewijs van opslag buiten Server4.
2. **Ondersteuning:** bepaal contactpersoon, contactgegevens, bereikbaarheid en responstijd; spreek onderhoud/storingsafhandeling en kosten af. Deze velden staan nog vast te stellen. Geen fictieve contactgegevens of servicebeloften.

### Wat later nodig is voor de eerste boekhoudkoppeling

De eigenaar bevestigde dat er nog geen pakket of bevoegde testomgeving is gekozen. Vraag de producteigenaar welk pakket de eerste beoogde klant gebruikt. Nodig: gekozen pakket/versie/importmogelijkheid, geautoriseerde testadministratie en toegang voor een aangewezen uitvoerder, stabiele debiteurmapping, dagboeken/grootboek/btw-codes, doelformaat/tekenconventie/afronding en aanpak voor duplicaten. Deel geen login/tokens via chat of Git.

Daarna één gecontroleerde fictieve batch importeren en uit het doelpakket teruglezen: aantallen, documentnummers, netto/btw, credits en oorspronkelijke facturen, betalingen/terugbetalingen en referenties, open posten en netto ontvangen geld. Bewaar import-ID/doelrapport, vergelijk vooraf vastgelegde totalen en onderzoek verschillen. Valideer deze ene koppeling volledig vóór meerdere pakketten. Download, intern kloppende CSV, lokale demonstratie-import of eigen verklaring telt niet als onafhankelijke externe validatie. Status blijft externe boekhoudimport niet gevalideerd.

## Tests en bewijs

18 gerichte automatische testgroepen slagen: 5 nieuwe proef-/winkel-/rechten-/administratiecontroles, 2 pure accountingadaptercontroles, 8 bestaande account/import/financiële/herstelregressies en 3 gedeelde-demotoegangregressies. De financiële correctie-/btw-/credits-/refundtests slagen eveneens. Zie delivery-test-results.txt, accounting-adapter-results.txt, regression-results.txt, demo-regression-results.txt en finance-results.txt. De pakketneutrale serializer werkt zonder actieve workflow en muteert de bronmomentopname niet. Een complete fictieve factuur/credit/betaling/refund blijft gekoppeld; netto omzet/geld zijn apart controleerbaar.

| Browsercontrole | Resultaat | Bewijs |
|---|---|---|
| Conceptvoorstel, open keuzes, eigenaar bewaart fictieve testkeuzes met bron, herladen | Geslaagd, alleen geïsoleerde testkopie | delivery-browser-results.json; proefvoorstel-1366.png |
| Monteur eigen opdracht vinden, 1 uur/Geen materiaal, gereedmelden en herladen | Geslaagd met echt fictief monteuraccount | proef-monteur.png |
| Winkel 5 beginvoorraad → verkoop 2 × €10 excl. → 1 retour/€12,10 refund → voorraad 4 | Geslaagd met apart fictief winkelaccount; ook dubbelklik | proef-winkel.png |
| Administratie overgenomen werk, €60 excl./€72,60 incl., definitief/fictief verzonden/betaald/afgesloten | Geslaagd met apart fictief administratieaccount | proef-administratie.png |
| Drie rolgebonden bevindingen vastleggen, geen acceptatie als demo-actor | Geslaagd in testkopie; geen echte medewerkersclaim | delivery-browser-results.json |
| 390 px proefpagina en behoud Toegang demo | Geslaagd; geen horizontale overloop | proefvoorstel-390.png |
| Live proefvoorstel, lege zakelijke keuzes, externe status open, 19 bronproblemen, JSON/CSV-ingangen, demo mag geen zakelijke keuzes wijzigen | Geslaagd; uitsluitend reads en demosessie/audit | live-browser-results.json, live-proefvoorstel-1366.png, live-proefvoorstel-390.png |
| Werkelijke menselijke medewerkersacceptatie | Niet getest | Technische browseraccounts tellen niet als echte medewerkers |
| Gekozen externe backup/herstel en boekhoudpakketimport | Niet ingericht/niet gevalideerd | Keuze/toestemming/toegang ontbreken volgens eigenaar |

Browsertests gebruiken Chromium/Playwright tegen een aparte kopie van de fictieve live bedrijfsstaat, vier afzonderlijke accounts en serverzijdige rechten. Voorbereiding via bestaande gevalideerde eigenaarhandelingen; uitvoering/overdracht/verkoop/retour/factuur/betaling/bevindingen via zichtbare bediening. Geen live testdossiers, prijzen, contactgegevens of acceptatieregistraties aangemaakt. Live keuzes en acceptatie zijn leeg.

## Gegevens en lokaal herstel

Live workflow vóór/na byte-identiek, SHA256 `4772b51acd7adca63ceab519c28744e7c9d8f157344b1a3eaca18b4aa5299f56`. De bestaande controle-CSV is ondanks de scheiding van de exportcode byte-identiek, SHA256 `975883d8806838cffb4fc8af736ada30ae10777115274b862daed28a4ce2f1d9`. Netto omzet €1.030,00; open debiteuren €473,40; netto ontvangen geld €772,90. Alle sluiten aan. De 19 bestaande bronproblemen blijven open, geen historische bronnen verzonnen.

Lokale snapshot: `/home/mau/server4-mobile-demo/backups/snapshot-20261027T160213961682Z/`. Op Server4 geïsoleerd hersteld: 11 dossiers, 138 historie-items en 6 reserveringen, volledige bedrijfstoestand en export gelijk. Herstelde app opent demo en proefvoorstel met juiste open externe status. Nieuwere geïsoleerde doeldata eerst behouden; gemanipuleerde backup vóór schrijven geweigerd. local-restore-results.json. Geen live restore of ongevraagde externe opslag gebruikt in de definitieve inrichting.

## Historische proef en correctie op nadere eigenaarinstructie

Vóór het antwoord op de bestemmingsvraag heb ik Server5 als tijdelijke proefbestemming gebruikt en een overdracht aan de bestaande dagelijkse taak gekoppeld. Dat liep vooruit op de nog ontbrekende keuze. Na de expliciete instructie is de koppeling volledig teruggedraaid: oorspronkelijke backupservice byte-identiek hersteld, timer behouden, ExecStartPost leeg en nieuw helperbestand uit scripts/ verwijderd. Geen verdere overdrachten. De tijdelijke versleutelde proefkopieën en uitsluitend daarvoor gegenereerde keys op Server5 zijn daarna binnen de eigen testscope verwijderd; originele Server4-data/backups bleven behouden. Niet-geheime historische testmetadata blijven lokaal als auditbewijs, niet als actuele externe voorziening. backup-owner-steering.json bewijst de eindtoestand. Het historische helperontwerp is alleen een .txt-bestand, geen actieve uitvoering.

De demo vermeldt daarom overeenkomstig de eigenaar: **externe back-up: nog niet ingericht en getest** voor een door hem gekozen bestemming. De historische technische proef is geen eigenaarkeuze, productie-inrichting of toekomstig schema. SSH-/Codex-authbestanden zijn niet gekopieerd. Geen credentials, private keys of appauthdatabases in Git/Notion. Geen nieuwe scheduler of achtergrondworker actief.

## Wijzigingen en rollback

Server4 gewijzigd/nieuw: accounting.py, delivery.py, secure_app.py, security.py, data.py, workflow.py, recovery.py, README.md, aankoopbeslissingen.md, proefvoorstel.md, backup-herstel.md, backup-config.example.json, static/proefvoorstel.html, static/delivery.js, static/index.html, static/pilot.html, static/pilot.js en static/praktijkproef.html. Geen nieuwe afhankelijkheden. Bronhashes in deployment-results.json/live-final-results.json. Bestaande dienst éénmaal gestopt/gestart voor bronpublicatie; monitoring en normale backups behouden. Recovery neemt de nieuwe bron en trial-data in workflow.json mee.

Herstelpunt bronnen: `/home/mau/server4-mobile-demo/backups/demo_conf_delivery_20261027_006/`. Stop de bestaande demo-userdienst, controleer latere wijzigingen, herstel alleen de gewijzigde bestaande bronbestanden en verwijder alleen de nieuw toegevoegde bronbestanden uit deze ronde als ze niet later zijn gewijzigd. Start dezelfde dienst en controleer /health, Toegang demo, cijfers en dossiers. Geen workflow-/accountrestore als onderdeel van bronrollback. Na gebruik van nieuwe winkelaccounts/trialregistraties moet een bronrollback hun compatibiliteit en rechten apart beoordelen; verwijder geen accounts/historie om terug te kunnen. Voor gegevensherstel is een afzonderlijke beslissing met vergelijking van nieuwere geschiedenis nodig.

Server5-backupservice/timer is na terugdraaien ongewijzigd ten opzichte van vóór deze taak; er blijft alleen lokale taakdocumentatie/Git en de bestaande mindmap voortgang bijgewerkt. Geen Notion-/andere externe publicatie volgens de eerdere demo-opdrachtgrens; geen publicatie of teruglezing geclaimd.

## Afsluiting

Succeeded voor de afgeronde fictieve demo-afwerking, met expliciet open zakelijke/externe besluiten. CLI zonder brokerrecord; geen brokerstatus vervalst. Current Projects 4 vóór → 6 tijdens → 4 na. Eigen taak/stap na bewijs gesnoeid, oude telefoonblokkade behouden. Eindvalidator en gepubliceerde bron: consistent=true, bronhash=publicatiehash, project_invariants_valid=true, iedere done-node een blad; final-validation.json/publication-check.json. Tijdelijke lokale testserver en SSH-testforward worden gestopt; bestaande Server4-dienst blijft actief.

Volgende stap: herlaad demo, kies **Proefvoorstel en acceptatie**. Bepaal externe back-upbestemming en ondersteuning afzonderlijk vóór echt gebruik. Boekhoudpakket/testomgeving later kiezen; tot die tijd pakket-onafhankelijke export en interne controles gebruiken met externe status niet gevalideerd. Echte deelnemers kunnen daarna onder hun eigen proefaccounts de routes beoordelen.
