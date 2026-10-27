# Demo-conf — dagelijks beslissen en verklaarbare geldstromen — 27 oktober 2026

**Uitgevoerd en live gecontroleerd.** Opdracht volgens de nieuwste /home/mau/demo-conf.md, bewaard als requirements.md. Taak demo_conf_daily_20261027_002. Hostname server5 en bestaande Git-wijzigingen vooraf gecontroleerd. Bestaande Server4-demo via de geautoriseerde SSH-route aangepast; geen nieuw dashboard, nieuwe permanente dienst of netwerkwijziging. Server4 heeft geen Git-repository of aanvullende AGENTS.md in de gecontroleerde app-/homemap. Eerder werk en alle live gegevens behouden.

## Wat verandert

- Compacte kop, navigatie, kerncijfers en aandachtspunten. Op 1366×768 staan de vier kerncijfers en de belangrijkste aandachtspunten tegelijk in beeld. Uitleg staat onder Info; roosterinstellingen staan onder Beschikbaarheid wijzigen. Browsercontrole op 1366, 760 en 390 pixels: geen horizontale paginaoverflow en geen JavaScript-fouten; screenshots visueel bekeken.
- Prioriteit met uitleg: **spoed → vervallen factuur/actie → geblokkeerd werk → administratie → inrichting**. Daarna de oudste bekende actiedatum/gereedmelding. Een dubbel werkprobleem krijgt één volgende actie; afzonderlijke facturen blijven apart.
- Factureerbaar werk toont gereedmelding, wachtdagen, conceptbedrag exclusief btw (of onbekend), verantwoordelijke en concrete vervolgactie. Historische afrondingsregistraties worden als bron benoemd; werkelijke uitvoeringsdatums worden niet verzonnen. Ontbrekende gereeddatum blijft onbekend. Aanvullen/corrigeren vereist een bron of reden en bewaart historie.
- De facturatieregel is bewust nog niet voor de eigenaar ingevuld. De inrichtingstaak vraagt het aantal dagen te kiezen; daarna wordt de interne actiedatum berekend. Een ingestelde regel blijft wijzigbaar via Voorraad & beheer. Geen klantdeadline verzonnen.
- Ontbrekende werktijden verschijnen eenmaal als roosterinrichtingstaak. Opslaan verwijdert de taak en herberekent capaciteit. De planning onderscheidt open afspraken, afgeronde/geregistreerde bezette bezoektijd, totale vrije tijd, resterende vrije tijd en onbekende inrichting. Geen open afspraken betekent niet automatisch vrij. De vaste demodag en zichtbare simulatietijd blijven leidend.
- **Ontvangsten = netto ontvangen geld inclusief btw, na terugboekingen en terugbetalingen.** Bank, kas, pin, methode onbekend en terugbetalingen zijn ieder doorklikbaar. Iedere lijst toont exact het subtotaal van haar registraties. Oorspronkelijke teruggeboekte ontvangst en tegenmutatie blijven zichtbaar en tellen samen nul.
- Dashboard, dossierbedragen, financiële demo-antwoorden en export gebruiken dezelfde definitie. Export behoudt bestaande velden en heeft aanvullend net_received_cents per factuur/verkoop en cashflow_effect_cents per getekende geldmutatie. Net_received_cents alleen op invoice/sale-ouderregels sommeren; cashflow_effect_cents over alle regels sommeren. Downloaden bevestigt geen boekhoudkundige verwerking.

## Het verschil van €344,60 verklaard

De bestaande live administratie is **ongewijzigd**. De volledige aansluiting is:

| Component | Bedrag incl. btw |
|---|---:|
| Bankontvangsten na terugboekingen, vóór terugbetalingen | €440,40 |
| Kas | €6,05 |
| Pin | €0,00 |
| Betaalmethode onbekend | €344,60 |
| Ontvangsten vóór terugbetalingen | €791,05 |
| Af: terugbetalingen | −€30,25 |
| **Netto ontvangen** | **€760,80** |

De eerdere bankweergave van €410,15 bevatte de bankterugbetaling al als aftrek. Nu staat die €30,25 afzonderlijk, zodat iedere component zichtbaar is. Er bestaat daarnaast een terugboeking van €50,00: de oorspronkelijke €50,00 plus tegenmutatie −€50,00 tellen nul; dit is geen extra terugbetaling. Geen ontbrekende betaalmethode ingevuld of bedrag verzonnen.

## Bedrijfsprocessen via de gebruikersinterface

Alle muterende proeven gebruiken een afzonderlijke fictieve kopie op Server5 en herkenbare TEST-dossiers. Geen live dossier gewijzigd door de acceptatietests. Dezelfde bestaande gebruikersschermen gebruikt, met automatische tussencontroles van dashboard, dossiers, voorraad, debiteuren en getekende export.

| Gevraagd scenario | Resultaat en concreet bewijs |
|---|---|
| 1. Voorraad reserveren, verbruiken en factureren | **Geslaagd.** Voorraad 5, reservering 2 → vrij 3; na vrijgave vrij 5; reservering/verbruik 1 → voorraad 4. Factuur €60 arbeid + €10 materiaal = €70 excl. / €84,70 incl. Zie browser-operations-results.json, materiaal-naar-factuur.png en route-manifest.json. |
| 2. Ontbrekend onderdeel inkopen, deelontvangst, vervolg | **Geslaagd.** Inkoop 2, ontvangst 1+1; diagnose en vervolg apart gepland, 0,5+1 uur; materiaal €15 → factuur €105 excl. / €127,05 incl. Zie inkoop-en-vervolg.png. |
| 3. Niet-gebruikt gereserveerd materiaal vrijgeven | **Geslaagd.** Reservering 2 vrijgegeven; vrije voorraad 3→5, geen onterechte afboeking; herhaalde vrijgave geweigerd. Stapfoto's 36/37 in route-manifest.json. |
| 4. Winkelverkoop en gedeeltelijke retour | **Geslaagd.** 2 stuks à €10,01 excl. verkocht; voorraad 3→1. Eerste retour van 1 → voorraad 2 en €12,11 fictief terugbetaald; tweede retour → voorraad 3 en totaal €24,22 terugbetaald. Dubbelklikken geeft geen dubbele mutatie. Stapfoto's 68/70/72 en winkelretour-voorraad-en-geld.png. |
| 5. Vaste offerteprijs met materiaal | **Geslaagd.** Afgesproken €100 excl.; 2 werkelijke uren en €25 geregistreerd materiaal blijven één factuurregel van €100 excl. / €121 incl. Geen dubbel materiaal of uurtarief. Zie browser-extra-results.json en route-stapfoto 109. |
| 6. Financiële correctie met oorspronkelijke registraties | **Geslaagd.** €20+€52,60 betaald, foutieve €20 teruggeboekt en correct opnieuw geregistreerd, saldo nul en herladen afsluiting behouden. Oorspronkelijke betaling en tegenmutatie blijven staan. Zie browser-operations-results.json. |

Zes geïsoleerde Python-suites slagen, met financiële afronding/btw/credits/refunds, statusovergangen, onbekende gegevens, prijsafspraken, revisies, aanvraagherhaling, tijdelijke opslagfout en backup/herstel. Gerichte daily-tests.py bewijst ook de volledige €760,80-aansluiting, pin/terugbetalingen, ontbrekende datums, prioriteitsvolgorde, bronhistorie, invoer-/rolgrenzen en verdwijnende inrichtingstaken. Zie unit-results.json en daily-results.json.

De browserlog bevat **122 geslaagde afstemmingscontroles**, waaronder 104 checkpoints bij knoppen en tien scenario-eindcontroles, plus dashboard-/instellings-/liveleestests. Geen muterende backendcalls gebruikt om gebruikersstappen over te slaan; API-reads controleren de uitkomsten. Zie step-reconciliation.jsonl, acceptance-results.json en settings-browser-results.json. De eindexport heeft 39 gekoppelde regels en twaalf ouderfacturen/-verkopen: unieke IDs, ouderrelaties, netto/btw/saldi en geldmutaties sluiten aan. Zie export-results.json en export-sample.csv; de volledige fictieve testhistorie staat in acceptance-final-state.json/test-state.json.

## Screenshots en live bewijs

Live dashboard: live/dashboard-1366.png, ook op 760/390. Live ontvangsten: live/ontvangsten-1366.png en live/ontvangsten-onbekend-1366.png, ook op 760/390. Capaciteit bij simulatietijd 17:00: live/capaciteit-17-uur.png. Volledige materiaal- en retourroute: materiaalroute.md, route-manifest.json en routes/. De extra instellingenproef staat in facturatie-prioriteiten.png.

Live browser-readback: live/dashboard-browser-results.json. Health en zes endpoints HTTP200; bron/assets geverifieerd. De workflow vóór/na is byte-identiek: SHA256 `934222da907ff39c5ef826a66fd0482a59440c80ef480a426e522856a0bb55a3`. Alle dossiers, histories, betalingsregistraties, roosters en voorraden behouden. Geen automatische live inrichting van Lina of facturatieregel. De eigenaar ziet deze bewuste open inrichtingstaken. Zie deployment-results.json en live-final-results.json.

Gewijzigde live bron in /home/mau/server4-mobile-demo: data.py, workflow.py, improvements.py, answers.py, static/app.js, static/style.css, static/index.html en README.md. Bestaande demo-userdienst eenmaal herstart; geen installatie, reboot of wijziging aan SSH/Tailscale/firewall/identiteiten. Tijdelijke testserver en loopback-SSH-forward worden na verificatie gestopt.

## Backup, rollback en resterende grenzen

Bronbackup vóór wijzigingen: `/home/mau/server4-mobile-demo/backups/demo_conf_daily_20261027_002/`. Definitieve bron plus ongewijzigde data: `/home/mau/server4-mobile-demo/backups/snapshot-20261027T070331490551Z/`. Alle dertien bestanden en manifesthashes gecontroleerd; snapshot bevat de definitieve bron en dezelfde workflow. Bestaande recovery.py dekt nieuwe regel-/datumhistorie via workflow.json; backup/monitoring niet vervangen.

Rollback: controleer latere wijzigingen; stop alleen server4-mobile-demo.service, herstel de acht genoemde gewijzigde bronbestanden uit de bronbackup en start dezelfde dienst. Controleer health, dossiers en bedragen. **Geen workflow-restore voor bronrollback**; herstel de workflow-reference.json niet blind over nieuwere historie. Original/ bewaart de oorspronkelijke bronnen ook op Server5.

**Open/niet getest:** externe boekhoudimport/koppeling, fysieke telefoon-/spraakacceptatie en nieuwe private HTTPS-toegang naar Server4. De browserproef via private SSH en lokale HTTP bewijst deze niet. Exports blijven fictieve controlegegevens, geen echte boekingen. Rollen zijn presentatie; één JSON-schrijfproces en backups op dezelfde host blijven demobeperkingen. De simulatietijd begint na herladen weer op 09:00; onbekende roosters en ontbrekende werkelijke datums vereisen bewuste inrichting. Geen onbeheerde Notion-synchronisatie geclaimd.

## Taakafsluiting

Succeeded. Current Projects: 4 nodes vóór → 6 tijdens → 4 na. Eigen taaknode en stap met bewijs gesnoeid; bestaande telefoonblokkade behouden. Eindvalidator: consistent=true, bronhash=publicatiehash, project_invariants_valid=true, iedere done-node een blad. CLI-opdracht zonder brokerrecord; alleen kaartstatus bijgewerkt. Tijdelijke testserver en SSH-forward gestopt.

Notion-snapshot gepubliceerd en teruggelezen: https://app.notion.com/p/406c7b03337681459f9ae96ef4397de2 ; centraal gedeeld werklog bijgewerkt. Geen permanente synchronisatie ingericht. Volgende stap: bestaande demo in browser herladen en het dashboard gebruiken; afzonderlijke telefoonblokkade blijft buiten deze opdracht.
