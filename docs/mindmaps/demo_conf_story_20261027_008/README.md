# Presentatie en gevulde standaarddemo — 27 oktober 2026, ronde 8

Actuele aanvulling op historische rondes hieronder. Zie demo-presentatie.md voor gebruik en resetgrenzen.

Nieuwe landing met Sleutelhuis-logo/merkhiërarchie, directe demoknop en medewerkersknop met afgeschermde-route-uitleg. Toegang demo start een vijfstaps native onboarding; de inhoudelijke dossier-rondleiding blijft aanwezig. Drie nieuwe fictieve verhalen en vijf voorraadartikelen worden éénmalig aan de bestaande data toegevoegd, zonder bestaande feiten/bedragen te veranderen. Herhaling van de inrichting maakt geen dubbele voorbeelden.

Eigenaar kan via de private accountwerkplek met één klik Reset demo uitvoeren: eerst volledige vorige bedrijfsstaat archiveren, daarna een gevulde standaard laden. Accounts en zakelijke beslissingen blijven bestaan. Oude proefuitslagen staan in het archief. Revisies en aanvraag-ID’s voorkomen stilzwijgende oude of dubbele opslag. Publieke bezoekers hebben geen toegang tot deze reset. Resetarchieven zijn onderdeel van recovery-backup/herstel; geen archiefgeschiedenis wordt automatisch verwijderd.

Concrete invoervalidatie, klantvriendelijke foutmeldingen en zichtbare laadstatus zijn toegevoegd; achtergrondpolls blijven stil. Mobiele landing plaatst de demoknop boven aanvullende kenmerken en alle onderdelen blijven leesbaar. Geen externe onboardinglibrary of nieuwe afhankelijkheden.

Deze ronde verandert geen productie-/support-/boekhoudbelofte: externe import niet gevalideerd, externe back-up nog niet ingericht/getest en ondersteuning nog vast te stellen. Bestaande geautoriseerde ngrok-route en private accounts blijven behouden.

---

# Praktijkproef en levering — 27 oktober 2026, ronde 6

Actuele aanvulling; vervangt historische uitspraken hieronder. /proefvoorstel bevat een concreet concept met voorbereiding, drie deelnemersroutes, criteria, zakelijke keuzes en evaluatie. Geen nieuwe dashboardfuncties. Prijs, periode en support blijven Nog vast te stellen totdat de eigenaar ze met bron vastlegt. Eigenaarinvoer is geen onafhankelijk bewijs van leveranciersinstemming.

Nieuw accounttype Winkelmedewerker (shop): eigen beperkte werkplek voor voorraad, fictieve contante verkoop en gedeeltelijke retour/terugbetaling; geen bedrijfsdashboard, klantdossiers, debiteuren, financiële export, tarieven of accountbeheer. Bestaande monteur/eigenaar/administratierechten blijven behouden. Deelnemers kunnen onder eigen account checklist/resultaat met bevindingen vastleggen. Dit zijn eigen verklaringen. Demo-/eigenaarbeoordelingen tellen niet als zelfstandige acceptatie door medewerkers. Technische browserproeven staan apart van echte medewerkersacceptatie. Toegang demo blijft werken.

Boekhouding is pakketneutraal: data.accounting_snapshot() bouwt een read-only domeinmomentopname. accounting.py serialiseert facturen, credits, betalingen, terugboekingen, refunds en winkelretouren zonder database-/netwerk-/bedrijfsregelimports. data.accounting_csv() blijft een compatibele ingang. Geen doelpakket aangenomen. Vraag de producteigenaar welk pakket de eerste klant gebruikt en of daarvoor een geautoriseerde testomgeving bestaat. Valideer daarna één koppeling volledig vóór meerdere pakketten. Tot die tijd blijft de status externe boekhoudimport niet gevalideerd. Boekhoudvoorbereiding toont bronproblemen en resterend mapping-/import-/afstemmingswerk; geen tijdwinst verzonnen.

**Externe back-up: nog niet ingericht en getest.** Geen gekozen/geautoriseerde externe bestemming in gebruik. Een instelbare bestemming en niet-actief configuratievoorbeeld zijn voorbereid; lokale snapshot en geïsoleerd herstel worden getest. De eerder tijdelijk toegevoegde Server5-overdracht is op nadere eigenaarinstructie teruggedraaid; de oorspronkelijke Server5 backupservice/timer is byte-identiek behouden. Historische proefartefacten blijven afgeschermd bewaard, zonder automatische vervolgoverdracht. Deze proef geldt niet als door eigenaar gekozen externe voorziening. Zie backup-herstel.md en backup-config.example.json.

Ondersteuning: contactpersoon, contactgegevens, bereikbaarheid en responstijd zijn **nog vast te stellen**. Geen externe dienst, contactgegevens of servicebelofte verzonnen. Back-upbestemming en ondersteuning worden als afzonderlijke eigenaarbeslissingen vóór echt bedrijfsgebruik opgeleverd. Ook kosten/contract, echte medewerkersacceptatie, boekhoudtest en privacy-/beheerafspraken blijven open. Productie is niet gereed.

---

 Directe demotoegang — 27 oktober 2026

Op /login opent **Toegang demo** zonder gebruikersnaam of wachtwoord de bestaande gedeelde fictieve administratie. De sessie heet Demobezoeker en is herkenbaar als demomodus; geen echt account of wachtwoord wordt aangemaakt. Demo-handelingen worden als demo-actor opgeslagen, niet als echte eigenaar. Bestaande dossiers blijven bewaard en demo-wijzigingen zijn gedeeld/persistent.

Gebruikersbeheer, accountaudit, stamgegevensimport en eigenaarsactivering zijn niet toegankelijk via deze demosessie. De bestaande gewone login en eenmalige eigenaaractivering blijven aanwezig. Afmelden trekt de demosessie serverzijdig in. De bestaande host-/origin-/JSON-/CSRF-controles blijven gelden; nieuwe zakelijke inhoud vereist nog steeds een sessie. Geen nieuwe publieke route/netwerktoegang. Deze knop geeft iedereen met bestaande private demotoegang toegang tot de fictieve bedrijfsroutes; gebruik deze gedeelde omgeving nooit voor echte bedrijfsdata. Geen bewijs van persoonlijke authenticatie via de knop.

---

# Actuele uitvoering — 27 oktober 2026, ronde 4

Deze sectie vervangt oudere uitspraken hieronder over ontbrekende appaccounts. Historische rondes blijven bewaard. Gebouwd voor begeleide fictieve praktijkproef; productie blijft niet gereed.

Startpunt `/login`. Eerste eigenaar: lees de eenmalige code in je eigen Server4-terminal met `cat ~/.local/state/server4-mobile-demo/owner-activation`, kies Eerste eigenaar inrichten en een eigen wachtwoord van minimaal 12 tekens, activeer en meld aan. Deel wachtwoord of code niet in chat. De activeringscode wordt na gebruik verwijderd; er is geen standaardlogin. Daarna onder Account, rechten en praktijkproef gebruikers aanmaken of beëindigen. Een gebruiker beëindigen trekt diens bestaande sessies meteen in. Afmelden maakt de huidige sessie ongeldig, ook bij hergebruik van de oude browsercookie. Sessies duren maximaal acht uur.

Werkzeug scrypt voor wachtwoordhashes; Flask ondertekent de sessiecookie met uitsluitend sessiereferentie/CSRF. De echte sessie is intrekbaar in SQLite; cookie HttpOnly/SameSite Strict. CSRF-token en oorsprongcontrole voor mutaties; host blijft localhost/127.0.0.1, geen nieuwe netwerkroute. Secure-cookie kan met DEMO_HTTPS=1 wanneer een echte HTTPS-route beschikbaar is; huidige SSH-tunnel gebruikt lokale HTTP. Geen claim van TLS/telefoonacceptatie. Geen openbare developmentserver: Waitress in één bestaande userdienst/proces, vier threads, bestaande workflowlock/revisie/atomic write.

Eigenaar: alle bestaande fictieve handelingen, instellingen, tariefbeheer, accounts en financiële correcties. Monteur: alleen toegewezen medewerkerdossiers en uitvoering/uren/toegewezen materiaal; geen financiële data-export, gebruikersbeheer of tarief-/betalingswijzigingen, ook niet via directe HTTP. Administratie: facturen, betalingen, debiteuren en export; wijzigingen van tarieven, materiaalprijzen en financiële correcties vereisen eigenaar. Bij nacalculatie gebruikt administratie alleen een reeds vastgelegd tarief en geregistreerde materiaalprijzen. Niet-geprijsd/los materiaal eerst door eigenaar laten controleren. De bestaande volledige werkplek voor administratie kan nog eigenaaracties tonen; server weigert die. Monteurs hebben een afzonderlijke beperkte werkplek.

Alle nieuwe workflowmutaties bewaren echte actor (user-ID/naam/rol/medewerker), bedrijfsdatum en werkelijk UTC-registratietijdstip in dezelfde atomaire bedrijfshistorie. Accounts/login/beëindigingen hebben afzonderlijke SQLite-audit. Oude acties blijven met oorspronkelijke demorol bewaard; geen identiteit achteraf verzonnen. Nieuwe definitieve facturen en verkoop/retouren bewaren ook afzonderlijke registratiestempels. CSV heeft een extra recorded_at-kolom; ontbrekende historische stempels blijven UNKNOWN.

Financiële afstemming en gecontroleerde migratie staan op `/pilot`; formaat/procedure in migratieformaat.md. Beginsaldi tellen mee bij debiteuren, niet bij nieuwe omzet of eerdere ontvangsten. De controle vergelijkt export met omzet/debiteuren/netto geld, bedragen, referenties en ontbrekende bronvelden. Source issues zijn open bronproblemen; balanced=true betekent niet dat externe import gereed of gevalideerd is.

Backups via `.venv/bin/python recovery.py`, met SQLite online backup voor gebruikers/audit, atomische bedrijfsstaat en sessiesleutel. Herstellen trekt browser-sessies in, behoudt eerst de huidige staat en controleert manifest vóór schrijven. Live herstel wordt geweigerd zolang de dienst draait. Externe kopie voorbereid: `.venv/bin/python recovery.py --external-destination /geautoriseerde/externe/mount`; alleen bestaande andere filesystem/mount, geen nieuwe externe infrastructuur. Geen externe bestemming geconfigureerd of geteste externe kopie geclaimd. Losse JSON en auth-SQLite hebben geen gedeelde cross-database-transactie; bedrijfshistorie zelf bevat de actor en vormt één consistente bedrijfsstaat.

Rollback van bron/dienst herstelt oude bron en de bewaarde serviceconfig, nooit blind workflow.json. Accounts/staat blijven bewaard. Oude bron schakelt echte appauth weer uit en valt terug op oude tunnel-/demogrenzen; gebruik bronrollback alleen bewust in die demoscope. Voor daadwerkelijk dataherstel: dienst stoppen, snapshot beoordelen, nieuwere geschiedenis vergelijken, herstel testen in afzonderlijke bestemming en pas daarna geautoriseerd live herstellen.

Nog nodig vóór echte bedrijfsafhankelijkheid: medewerkersacceptatie, externe backup/periodieke herstelcontrole, boekhoudtesttenant/importbewijs, echte bronmapping/migratiebesluit, prijs/contract, aanspreekpunt/support en hosting/privacy-/beveiligingsafspraken. Geen MFA, selfservice wachtwoordherstel, beschikbaarheidsgarantie of productiecertificering geclaimd. Commerciële beslislijst: aankoopbeslissingen.md.

---

# Sleutelhuis — lokale fictieve bedrijfsdemo

Bestaande Python-app op server4, nu met Flask/Werkzeug en Waitress, uitsluitend 127.0.0.1:8764; bestaande private toegang behouden. Demodag 26 oktober 2026, Europe/Amsterdam. Echte accounts bepalen serverzijdige toegangsrechten. De historische rolkeuzes zijn uitsluitend presentatie en geven geen extra rechten. Bestellingen, verzending, betalingen en terugbetalingen zijn uitsluitend lokale registraties, geen externe handelingen.

## Bediening
Nieuwe opdracht of offerte → dossier → planning → werkregistratie/concept → gereed → prijsafspraak/factuurcontrole → definitief → fictieve verzending → betalingen → administratief afsluiten. Bij offerte: leg de afrekenvorm vast vóór uitvoering. Direct opdrachtakkoord heeft afzonderlijke naam/datum/referentie. Een vaste prijs bevat het afgesproken materiaal; werkelijk verbruik blijft zichtbaar in het dossier en wordt niet opnieuw opgeteld. Meerwerk heeft een afzonderlijk bedrag, omschrijving en goedkeuring.

Definitieve factuurbedragen blijven behouden. Onder financiële correcties: betaling terugboeken met reden, gedeeltelijke/gehele credit en eventueel terugbetalen van klanttegoed. Volledig gecrediteerd en financieel vereffend origineel kan een vervangend concept opleveren met verwijzing; origineel blijft terugvindbaar. Overbetalingen zijn geblokkeerd. Afgesloten dossiers eerst met reden heropenen. Afsluiting blokkeert bij open saldo, klanttegoed of onopgeloste controles.

In dossier: vrije voorraad, reserveren, verbruiken, ongebruikte reservering vrijgeven. Inkoop ondersteunt deelontvangst; ontvangst wordt niet automatisch verbruik. Materiaalretour na facturatie vereist toereikende creditreferentie; bij concept eerst corrigeren. Winkelretour boekt voorraad en fictieve kas-terugbetaling met btw. Garantie en annulering behouden hun historie. Concepten en werkelijke bezoekuren zijn apart bewaard.

## Boekhoudgrens
CSV via /api/accounting-export bevat facturen, creditregels, betalingen, terugboekingen, refunds, winkelretouren, originele nummers, datum, EUR, bedragen in gehele centen en bronhash waar beschikbaar. UNKNOWN betekent daadwerkelijk ontbrekende informatie. Downloaden wijzigt geen verwerkingsstatus. Dossier kent nog te verwerken, export geregistreerd, handmatig bevestigd met bewijsreferentie en fout/afstemming. Financiële wijzigingen maken een eerdere bevestiging opnieuw afstemmingsplichtig.

Voorbereid doelpakket voor een toekomstige proef: e-Boekhouden.nl. Dit is GEEN gevalideerd importbestand voor dat pakket. Voor import: debiteuren matchen op stabiele externe IDs, factuurdatums en nummers valideren, dagboeken/grootboek/btw-codes en tekenconventie vastleggen, record_types splitsen, centen naar decimalen omzetten, betalingen/credits koppelen, daarna een afgeschermde proefimport op aantallen/netto/btw/debiteuren afstemmen. Pas na externe controle en een teruggelezen pakketreferentie handmatig verwerking bevestigen. Toegang en externe proefimport zijn niet uitgevoerd of geautoriseerd.

## Opslag, backup en herstel
Workflow: ~/.local/state/server4-mobile-demo/workflow.json, tegelconfig: tiles.json. Eén bestaande Python-service met threading.RLock en revisiecontrole; schrijven via tijdelijk bestand + fsync + atomic replace. Verouderde revisies worden geweigerd; onopgeslagen invoer blijft bij conflict zichtbaar. Schone dossiers pollen elke twee seconden. Geen garantie op schaalbaarheid, meerdere serverprocessen of productiebeveiliging; alle gebruikers delen dezelfde demostaat.

Maak lokale gecontroleerde backup met `python3 recovery.py`. Deze bewaart applicatiebron, workflow en tegelconfig met SHA256-manifest onder backups/snapshot-UTC. Appaccounts en lokale sessiesleutel zijn nu inbegrepen; behandel deze backup als vertrouwelijk (0700 map, 0600 staat). Codex-/SSH-authbestanden worden nooit meegenomen. Een backup op dezelfde schijf beschermt niet tegen schijfverlies; er is geen nieuwe externe of periodieke backup geclaimd.

Herstel: stop `systemctl --user stop server4-mobile-demo.service`; controleer en kies snapshot; voer `python3 recovery.py --restore /volledig/pad/naar/snapshot --service-stopped` uit; start dienst en controleer /health, dossiers, totaalbedragen en historie. Manifest wordt vóór schrijven gecontroleerd; actuele bestanden worden eerst in before-restore-UTC bewaard. Herstellen wist geen historiebackup, maar zet de actieve toestand terug: stem nieuwere gebruikerswijzigingen eerst af. Geen live restore uitgevoerd; geïsoleerde herstelproef geslaagd.

## Praktijkgrens
Echte gebruikersauthenticatie en beperkte rollen beschikbaar; geen boekhoud-/bank-/mail-/leverancierskoppeling, kostprijsadministratie, volledige stamgegevens of fiscale productiegoedkeuring. Marge blijft onbekend zolang inkoop-, loon- en overheadkosten ontbreken. Bestaande telefoon/spraakacceptatie is een afzonderlijke open taak. Gebruik uitsluitend fictieve gegevens.

## Praktijkproefronde 2 — 26 oktober 2026

Dossierkop, dashboard en lijsten delen de statusafleiding. Opdrachtstatus, factuurstatus, betalingsstatus en boekhoudstatus zijn afzonderlijk zichtbaar. Klanttegoed opent de terugbetaalroute, heropenen toont opnieuw in behandeling, en een definitieve factuur heet geen conceptbedrag. De compacte samenvatting bovenaan bevat afspraak, verantwoordelijke, prijsafspraak, bedragen en vervolgactie. Factuurregels staan eenmaal uitgewerkt; historie en correcties zijn apart raadpleegbaar.

Historische betalingen hebben een stabiele interne referentie, ook wanneer oorspronkelijk geen nummer bestond. Bij ‘Betaalgegevens aanvullen / corrigeren’ blijven bedrag en origineel behouden, met reden en voor/na-historie. Kies alleen ‘Aangetoond met bron’ als datum, methode en referentie werkelijk beschikbaar zijn. Kies anders ‘Brongegevens ontbreken / onvoldoende’ en laat onbekende velden leeg. Een bedrag terugboeken is een afzonderlijke actie. Dit kan ook na een terugbetaling; het daaruit volgende saldo moet opnieuw worden afgehandeld. Een verschil tussen ontvangen totaal en betalingsregistraties blokkeert afsluiten. Er wordt geen sluitboeking verzonnen.

Iedere nieuwe interfaceaanvraag krijgt een uniek nummer. De workflow bewaart een ontvangstbewijs met payloadhash; dezelfde aanvraag kan na een verloren antwoord veilig opnieuw worden aangeboden, ook als de revisie intussen is gestegen. Hergebruik met andere inhoud wordt geweigerd. Opslagfouten tonen een foutmelding en laten invoer staan. Dit beschermt binnen de bestaande service; meerdere onafhankelijke schrijfprocessen zijn niet ondersteund.

De controle-export bevat nu stabiele betalingsnummers, parent_payment, metadatacorrecties, expliciete ontbrekende velden en noodzakelijke mappings. Winkelverkoop, ontvangst, retour en terugbetaling hebben afzonderlijke gekoppelde regels. Omzet, netto-ontvangsten en saldi zijn lokaal tegen het dashboard afgestemd. Externe importvalidatie blijft open; downloaden verandert nooit de verwerkingsstatus.

Bij een actief onderdeeltekort volgt de stappenhulp de actuele inkoop-, ontvangst- of vervolgplanningsstap. Gereedmelden vóór volledige ontvangst en vervolgplanning wordt geweigerd; een diagnose kan tussentijds als concept worden bewaard.

## Werkplekronde 3 — compact dossier, acties en teamrooster

Het dossier heeft één compacte samenvatting en één primaire vervolgactie. Uitgebreide invoer staat onder Uitvoering en materiaal, Documenten en boekhouding, Betalingen en correcties, en Historie. Betalingen heten naar hun bedrag; datum en referentie ondersteunen de keuze. Interne betalingsnummers staan alleen in technische details. Een teruggeboekte betaling blijft in Historie en telt niet meer als actieve bronwaarschuwing.

‘Methode niet vastgelegd’ op het dashboard opent de betreffende actieve betalingen. Kies een registratie om brongegevens rechtstreeks aan te vullen; dit verandert geen bedrag en kan ook bij een financieel gesloten dossier. Voor een bedragcorrectie heropen je het dossier expliciet. Betaalgegevens van een eerdere factuur blijven vanuit dezelfde waarschuwing herstelbaar nadat een vervangende factuur is gemaakt. Er worden geen ontbrekende gegevens verzonnen.

Gebruikelijke werktijden worden expliciet ingericht via de medewerkerskaart op het dashboard. ‘Vul fictief voorbeeld in’ vult alleen het formulier; opslaan blijft een bewuste handeling met bron/toelichting. Een dagafwijking gaat vóór het gebruikelijke rooster. Een bekende niet-werkdag heeft nul capaciteit; ontbrekende inrichting blijft onbekend. Pauze, afwezigheid en aan een afspraak gekoppelde reistijd worden afgetrokken. Afgeronde bezoeken blijven in de daghistorie; hun vastgelegde afspraakvakken tellen niet opnieuw als vrije tijd. De beschikbaarheid is gebaseerd op ingevoerde roosters en afspraakvakken, niet op een live tijdregistratie of automatisch berekende reistijd. Bezoeken zonder vastgelegde datum/tijd worden niet op een verzonnen dag geplaatst.

Deze velden staan in de bestaande workflow.json en vallen mee in recovery.py. Geen extra service of opslagdatabase. Een contante winkelverkoop telt als kasontvangst, ook bij oudere verkooprecords; een ontbrekende historische verkoopdatum blijft onbekend. Omzet, ontvangsten en saldi blijven van boekhoudverwerking onderscheiden. Externe importvalidatie blijft open.

## Dashboardronde — 27 oktober 2026

De demodag blijft maandag 26 oktober 2026. Bedrijfsdatums voor automatische factuur-, ontvangst-, verkoop- en dossieracties en de controle op factuuropvolging gebruiken dezelfde vaste dag als het dashboard; de echte UTC-tijd blijft behouden in auditstempels. Handmatig vastgelegde datums/historie worden niet herschreven.

Boven de compacte personeelsplanning staan unieke aandachtspunten met klant, verantwoordelijke, deadline (of expliciet onbekend), relevant open bedrag en één directe actie. Betaalgegevens controleren telt unieke actieve betalingen; filters op methode, referentie, bronbevestiging en datum kunnen overlappen. Teruggeboekte registraties blijven historisch bewaard. Metadata aanvullen verandert geen geldbedragen.

Capaciteit staat in uren en minuten. Totale vrije tijd betreft de hele demodag; nog beschikbare tijd begint op het zichtbare simulatietijdstip (standaard 09:00, zelf te wijzigen). De echte klok stuurt dit niet. Ontbrekende roosters/duur blijven onbekend. De volledige tijdlijn en afgeronde bezoeken staan onder een uitklaponderdeel; afgeronde tijd blijft bezet. Gebruikelijke roosters en dagafwijkingen blijven instelbaar.

Bronrollback: herstel uitsluitend gewijzigde bronbestanden uit backups/demo_conf_dashboard_20261027_001 na controle op latere wijzigingen en herstart de bestaande userdienst. De workflow.json hoeft voor bronrollback niet te worden teruggezet. Gebruik recovery.py uitsluitend voor afzonderlijk bewust gegevensherstel; behoud de voor-herstelbackup en nieuwere historie.

## Dagelijks dashboard — 27 oktober 2026, ronde 2

Kerncijfers en de belangrijkste aandachtspunten staan compact bij elkaar. Prioriteit is expliciet: spoed → vervallen factuur/actiedatum → geblokkeerd werk → administratie → ontbrekende inrichting. De eigenaar kan een interne facturatieregel van 0–90 dagen vastleggen; zonder regel wordt geen deadline verzonnen en staat er een inrichtingstaak. Voor gereed werk worden gereedmelding, wachtdagen, conceptbedrag (excl. btw) of onbekend, verantwoordelijke en vervolgstap getoond. Historische gereedmeldingen komen uit de gedateerde afrondingshistorie; deze bron wordt vermeld en is geen aanname over de werkelijke uitvoeringsdag. Bewuste datumcorrecties vereisen een bron/reden en bewaren voor/na-historie. Nieuwe gereedmeldingen slaan de vaste demodag op, met afzonderlijke echte UTC-auditstempel.

Ontbrekende werktijden geven één roosterinrichtingstaak per medewerker. Na opslaan verdwijnen die taak en de onbekende capaciteit. Instellingen staan onder Beschikbaarheid wijzigen. Planning maakt onderscheid tussen open afspraken, geregistreerde/afgeronde bezette bezoektijd, totale vrije tijd en vrije tijd vanaf het zichtbare simulatietijdstip; een lege lijst open afspraken betekent niet automatisch vrije capaciteit.

**Ontvangsten betekent netto ontvangen geld inclusief btw, na terugboekingen en terugbetalingen.** Bank + kas + pin + methode onbekend geven de ontvangsten na terugboekingen, vóór terugbetalingen. Trek de afzonderlijke terugbetalingen daarvan af om het netto totaal te krijgen. Iedere categorie toont de onderliggende getekende geldmutaties en het exact bijbehorende subtotaal. Oorspronkelijke teruggeboekte registraties blijven naast hun tegengestelde mutatie bestaan en tellen samen nul. Terugbetalingen zijn een andere mutatiesoort. Ontbrekende betaalmethoden worden niet ingevuld of als bank/kas aangenomen.

De CSV behoudt bestaande kolommen en relaties. received_cents is ontvangen vóór terugbetaling, refund_cents de terugbetaalde som. De nieuwe kolom net_received_cents is hun verschil per factuur/verkoop; cashflow_effect_cents bevat uitsluitend het getekende geld-effect van een ontvangst, terugboeking of terugbetaling (andere regels nul). Sommeer cashflow_effect_cents over alle regels voor het dashboardtotaal; sommeer net_received_cents alleen op de oorspronkelijke invoice/sale-ouderregels om herhaling te vermijden. Credits veranderen omzet/saldo, geen bank/kas zonder afzonderlijke refund. Downloaden wijzigt geen verwerkingsstatus. Externe import blijft ongevalideerd.

Herstelpunt vóór deze ronde: backups/demo_conf_daily_20261027_002. Bronrollback herstelt uitsluitend de gewijzigde bronbestanden, na controle op latere wijzigingen en met de bestaande demo-userdienst gestopt. Geen workflow-restore nodig voor bronrollback; nieuwe datumhistorie, regelinstellingen en dossiers blijven in workflow.json bewaard. Bestaande recovery.py neemt de gewijzigde bron en alle nieuwe taakgegevens in diezelfde opslag mee.

## Verkoopdemonstratie — 27 oktober 2026, ronde 3

Gebruik Rondleiding voor drie routes in de bestaande werkplek: monteur (offerte tot betaald/afgesloten), ontbrekend onderdeel (diagnose/deellevering/vervolg/factuur), winkelbalie (zoeken/voorraad/verkoop/deelretour/terugbetaling). De pagina Praktijkproef en aanschaf staat op /praktijkproef. Zij beschrijft uitsluitend bewezen demofuncties en markeert ontbrekende prijs-, contract-, beveiligings- en ondersteuningsafspraken als Nog vast te stellen. Geen externe verwerking, verzending of tijdwinstclaim.

Zet drie oefenroutes klaar maakt bewust twee nieuwe fictieve dossiers en vier exemplaren van een uniek oefenartikel. Nieuwe oefenronde maken wist niets: eerdere rondes, dossiers, voorraden en histories blijven bewaard. De rolkeuze is presentatie, geen gebruikersauthenticatie. Werk uitsluitend met fictieve gegevens.

Materiaal vrijgeven en retourneren opent nu een formulier met hoeveelheid en reden. Gedeeltelijke vrijgave verlaagt alleen de actieve reservering; voorraad wordt niet bijgeteld. Materiaalretour verhoogt voorraad en verlaagt het nog verbruikte aantal met behoud van oorspronkelijke hoeveelheid en transitiehistorie. Een herleidbare materiaalregel in een concept wordt gecontroleerd aangepast; vaste prijs/afzonderlijk goedgekeurd meerwerk blijven de afspraak volgen. Na definitieve facturatie vereist retour een toereikende creditreferentie; definitieve regels worden nooit stilzwijgend veranderd. Dubbele aanvraag, te grote aantallen en onvoldoende credit worden geweigerd of als dezelfde aanvraag herkend.

Retourhistorie toont artikel, aantal, datum, reden, bedrag, betaalmethode en oorspronkelijke verkoop. De meest recente opslaghandeling heeft één zichtbare succes-/foutmelding. Verloren antwoorden en tijdelijke fouten behouden invoer; dezelfde aanvraag kan veilig opnieuw worden aangeboden. Conflicten vereisen verversen en behouden eigen onopgeslagen tekst.

Nieuwe definitieve facturen krijgen de vaste demodag als factuurdatum. Ontbrekende historische factuurdatums blijven onbekend tot een gebruiker een bewezen datum en bron vastlegt. De oorspronkelijke ontbrekende waarde en correctie blijven in date_history en als invoice_date_metadata in de export staan. Bekende definitieve datums worden niet overschreven. Een eigen verklaring met bewijsreferentie is geen onafhankelijk gevalideerde externe boekhoudverwerking; downloaden wijzigt geen status.

Backup/restore via recovery.py omvat nu ook sales.py en static/praktijkproef.html, naast workflow.json met nieuwe rondes, datum- en materiaalhistorie. Herstel eerst geïsoleerd en behoud nieuwere gegevens via de voor-herstelbackup. Snapshot op dezelfde host is geen externe rampenbackup. Bronrollback vanuit backups/demo_conf_sales_20261027_003 herstelt uitsluitend de gewijzigde bestaande bronnen en verwijdert alleen de twee in deze ronde nieuw toegevoegde bronbestanden nadat latere wijzigingen zijn beoordeeld; geen workflow-restore nodig.

Productie vergt nog echte accounts/rechten, privacy/beveiligingsbeoordeling, gevalideerde koppelingen/import, externe backup/beheer en commerciële afspraken. Begeleide fictieve praktijkproef en verkoopdemo worden afzonderlijk van productie beoordeeld. Zie het taakverslag en aankoopbeslissingen.md in de Server5-documentatie.
