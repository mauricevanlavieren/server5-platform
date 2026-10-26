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
