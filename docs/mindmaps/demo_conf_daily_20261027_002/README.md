# Sleutelhuis — lokale fictieve bedrijfsdemo

Bestaande Python-stdlibapp op server4, uitsluitend 127.0.0.1:8764; bestaande private toegang behouden. Demodag 26 oktober 2026, Europe/Amsterdam. Rollen zijn demonstratiekeuzes, geen accounts of toegangsbeveiliging. Bestellingen, verzending, betalingen en terugbetalingen zijn uitsluitend lokale registraties, geen externe handelingen.

## Bediening
Nieuwe opdracht of offerte → dossier → planning → werkregistratie/concept → gereed → prijsafspraak/factuurcontrole → definitief → fictieve verzending → betalingen → administratief afsluiten. Bij offerte: leg de afrekenvorm vast vóór uitvoering. Direct opdrachtakkoord heeft afzonderlijke naam/datum/referentie. Een vaste prijs bevat het afgesproken materiaal; werkelijk verbruik blijft zichtbaar in het dossier en wordt niet opnieuw opgeteld. Meerwerk heeft een afzonderlijk bedrag, omschrijving en goedkeuring.

Definitieve factuurbedragen blijven behouden. Onder financiële correcties: betaling terugboeken met reden, gedeeltelijke/gehele credit en eventueel terugbetalen van klanttegoed. Volledig gecrediteerd en financieel vereffend origineel kan een vervangend concept opleveren met verwijzing; origineel blijft terugvindbaar. Overbetalingen zijn geblokkeerd. Afgesloten dossiers eerst met reden heropenen. Afsluiting blokkeert bij open saldo, klanttegoed of onopgeloste controles.

In dossier: vrije voorraad, reserveren, verbruiken, ongebruikte reservering vrijgeven. Inkoop ondersteunt deelontvangst; ontvangst wordt niet automatisch verbruik. Materiaalretour na facturatie vereist toereikende creditreferentie; bij concept eerst corrigeren. Winkelretour boekt voorraad en fictieve kas-terugbetaling met btw. Garantie en annulering behouden hun historie. Concepten en werkelijke bezoekuren zijn apart bewaard.

## Boekhoudgrens
CSV via /api/accounting-export bevat facturen, creditregels, betalingen, terugboekingen, refunds, winkelretouren, originele nummers, datum, EUR, bedragen in gehele centen en bronhash waar beschikbaar. UNKNOWN betekent daadwerkelijk ontbrekende informatie. Downloaden wijzigt geen verwerkingsstatus. Dossier kent nog te verwerken, export geregistreerd, handmatig bevestigd met bewijsreferentie en fout/afstemming. Financiële wijzigingen maken een eerdere bevestiging opnieuw afstemmingsplichtig.

Voorbereid doelpakket voor een toekomstige proef: e-Boekhouden.nl. Dit is GEEN gevalideerd importbestand voor dat pakket. Voor import: debiteuren matchen op stabiele externe IDs, factuurdatums en nummers valideren, dagboeken/grootboek/btw-codes en tekenconventie vastleggen, record_types splitsen, centen naar decimalen omzetten, betalingen/credits koppelen, daarna een afgeschermde proefimport op aantallen/netto/btw/debiteuren afstemmen. Pas na externe controle en een teruggelezen pakketreferentie handmatig verwerking bevestigen. Toegang en externe proefimport zijn niet uitgevoerd of geautoriseerd.

## Opslag, backup en herstel
Workflow: ~/.local/state/server4-mobile-demo/workflow.json, tegelconfig: tiles.json. Eén bestaande Python-service met threading.RLock en revisiecontrole; schrijven via tijdelijk bestand + fsync + atomic replace. Verouderde revisies worden geweigerd; onopgeslagen invoer blijft bij conflict zichtbaar. Schone dossiers pollen elke twee seconden. Geen garantie op schaalbaarheid, meerdere serverprocessen of productiebeveiliging; alle gebruikers delen dezelfde demostaat.

Maak lokale gecontroleerde backup met `python3 recovery.py`. Deze bewaart applicatiebron, workflow en tegelconfig met SHA256-manifest onder backups/snapshot-UTC. Geen authbestanden. Een backup op dezelfde schijf beschermt niet tegen schijfverlies; er is geen nieuwe externe of periodieke backup geclaimd.

Herstel: stop `systemctl --user stop server4-mobile-demo.service`; controleer en kies snapshot; voer `python3 recovery.py --restore /volledig/pad/naar/snapshot --service-stopped` uit; start dienst en controleer /health, dossiers, totaalbedragen en historie. Manifest wordt vóór schrijven gecontroleerd; actuele bestanden worden eerst in before-restore-UTC bewaard. Herstellen wist geen historiebackup, maar zet de actieve toestand terug: stem nieuwere gebruikerswijzigingen eerst af. Geen live restore uitgevoerd; geïsoleerde herstelproef geslaagd.

## Praktijkgrens
Geen echte gebruikersauthenticatie, boekhoud-/bank-/mail-/leverancierskoppeling, kostprijsadministratie, volledige stamgegevens of fiscale productiegoedkeuring. Marge blijft onbekend zolang inkoop-, loon- en overheadkosten ontbreken. Bestaande telefoon/spraakacceptatie is een afzonderlijke open taak. Gebruik uitsluitend fictieve gegevens.

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
