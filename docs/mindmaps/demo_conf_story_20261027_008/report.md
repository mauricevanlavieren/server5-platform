# Demo aangepast volgens demo-conf.md — 27 oktober 2026

Status: uitgevoerd en live. Open https://prognosis-energize-calzone.ngrok-free.dev/login en kies **Toegang demo**. De opgeslagen requirements.md bevat de gebruikte opdracht.

## Resultaat

De startpagina heeft een eigen Sleutelhuis-logo, duidelijke demo-ingang en een informatieve knop voor de private medewerkersroute. De demo start met een overslaanbare rondleiding van vijf stappen die de bestaande bediening markeert; opnieuw openen kan via Snelle rondleiding. De bestaande inhoudelijke Rondleiding blijft beschikbaar.

Drie fictieve dossiers zijn toegevoegd: Familie Janssens (spoed), VvE Parkzicht (geaccepteerd onderhoud) en Bakkerij De Hoek (wacht op onderdeel). Live zijn dat W117–W119. Vijf voorraadproducten ondersteunen het verhaal. Het ontbrekende maatwerkonderdeel 40/50 staat bewust niet op voorraad; de aanwezige standaardcilinder 30/35 is een ander artikel. Die samenhang is apart gecontroleerd en de correctie is met behoud van auditgeschiedenis aangebracht.

De interface bevat laadindicatoren en begrijpelijke invoer- en netwerkfouten. De mobiele landing en het dashboard passen ook op 320 pixels. Bestaande facturen en financiële cijfers worden uit de bestaande administratie getoond: omzet €1.040, netto ontvangen €785 en open €473,40. De pakket-onafhankelijke financiële export is byte-identiek gebleven.

## Reset en gegevensbehoud

Reset demo is uitsluitend beschikbaar voor de eigenaar via de private account-/praktijkpagina. Publieke bezoekers kunnen deze actie en het accountbeheer niet gebruiken. Reset archiveert eerst de volledige vorige bedrijfsstaat op dezelfde host, bewaart accounts en commerciële keuzes en gebruikt revisiecontrole en een herhaalveilig verzoeknummer. Een verloren antwoord veroorzaakt bij opnieuw proberen geen tweede reset. Andere geopende schermen herkennen de nieuwe demoversie; onopgeslagen invoer blijft beschermd tegen stil overschrijven.

Bij deze uitrol is de live administratie NIET gereset. Nieuwe voorbeelden zijn toegevoegd; bestaande orders, dossiers, voorraad, tarieven en histories zijn behouden. De laatste live controle constateerde nul resets. Workflowrevisie ging van 175 naar 177 door de toevoeging en de samenhangcorrectie. Authbestanden bleven op Server4 en zijn niet naar deze repository gekopieerd.

## Bewijs

- Twintig automatische unittestgroepen geslaagd: vijf nieuwe groepen, acht bestaande account/import/herstelgroepen, drie demotoeganggroepen en vier publieke toegangscontroles. Financiële controleproeven eveneens geslaagd.
- Vijf geïsoleerde browsergroepen geslaagd, inclusief invoerherstel, laadindicatoren, volledige rondleiding, reset met vier fictieve accounts en herhaling na verloren resetantwoord.
- De echte publieke HTTPS-route is met een browser gecontroleerd: landing, toegang, rondleiding, dossiers, mobiele weergave en blokkering van private beheerroutes. Dit is onderscheiden van de lokale HTTP-proeven.
- Schermformaten 320, 390 en 1366 pixels gecontroleerd. Screenshots en JSON/testresultaten staan in deze map.
- Alle achttien uitgerolde bronbestanden komen overeen met de gecontroleerde bestanden. De dienst is actief. Zie deployment-results.json, live-final-results.json en scenario-review-results.json.
- De definitieve lokale back-up met veertig bestanden is op Server4 geïsoleerd hersteld. De bedrijfsstaat was byte-identiek. Vervolgens zijn reset, exacte archivering, accountbehoud, opnieuw back-uppen en opnieuw herstellen inclusief resetarchief getest. Geen live reset uitgevoerd. Zie local-restore-results.json.

## Grenzen en open besluiten

Externe boekhoudimport blijft **niet gevalideerd**; er is geen pakket gekozen. Voor validatie zijn later het gekozen pakket, importformaat/API-documentatie en een geautoriseerde testomgeving nodig.

Externe back-up blijft **nog niet ingericht en getest**. De back-ups en resetarchieven hierboven staan op dezelfde Server4-host en vervangen geen externe bestemming. De eigenaar moet die bestemming vóór echt bedrijfsgebruik kiezen en toestemming geven.

Ondersteuning: contactpersoon, contactgegevens, bereikbaarheid en responstijd blijven **nog vast te stellen**. Dit is de tweede afzonderlijke beslissing vóór echt bedrijfsgebruik. Er zijn geen servicebeloften toegevoegd.

De bestaande publieke ngrok-route en SSH-forward zijn behouden. Geen router-, SSH-authenticatie-, firewall- of sudoerswijzigingen, reboot of nieuwe infrastructuur. Documentatie blijft lokaal/Git volgens de demo-opdracht; geen externe documentpublicatie voor deze wijziging.

## Bestanden en rollback

De achttien bestanden staan met SHA256 in deployment-results.json. changes.diff toont het verschil met original/. Hoofdwijzigingen: demo_story.py, secure_app.py, data.py, business.py, recovery.py en de statische interface. README.md en demo-presentatie.md beschrijven gebruik.

Server4 bewaart de volledige toestand vóór deze taak onder /home/mau/server4-mobile-demo/backups/demo_conf_story_20261027_008/before-complete, oorspronkelijke gewijzigde bronnen onder source-before en de laatste geteste snapshot onder /home/mau/server4-mobile-demo/backups/snapshot-story-final-1793124046940309725.

Voor bronrollback: stop server4-mobile-demo.service, beoordeel eventuele latere wijzigingen, herstel alleen de betrokken oorspronkelijke bronbestanden en verwijder alleen de drie nieuw toegevoegde bestanden indien ze daarna niet verder zijn gebruikt; start de dienst weer en controleer gezondheid. Behoud accounts, bedrijfsgegevens en resetarchieven. Gebruik na resets compatibele herstelsoftware die de archieven meeneemt. Zet niet zonder afzonderlijk herstelbesluit de oude bedrijfsstaat terug: daarmee kunnen latere gebruikerswijzigingen verdwijnen. De bewaarde volledige back-up maakt zo'n gecontroleerd herstel mogelijk.

## Taakregistratie

CLI-taak demo_conf_story_20261027_008 heeft geen brokerrecord. Current Projects: vier nodes vóór, zes tijdens en vier na afronding; bestaande telefoonblokkade en histories blijven behouden. De eindvalidator en HTTP-teruglezing worden apart opgeslagen. Alleen de eigen lokale testserver wordt gestopt; de live dienst, forward en ngrok blijven beschikbaar.
