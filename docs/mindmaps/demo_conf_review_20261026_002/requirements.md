Je werkt verder aan de bestaande Server4-demo voor een sleutelservice, winkel in hang- en sluitwerk en toegangscontrole. Neem twee perspectieven aan: Henk, de eigenaar die overzicht en tijdwinst nodig heeft, en de softwareontwikkelaar die betrouwbare bedrijfsprocessen bouwt.
Voer de verbeteringen daadwerkelijk uit in de bestaande applicatie. Behoud wat al werkt. Het doel van deze ronde is de resterende onzekerheden weg te nemen voordat Henk een praktijkproef begint.
Wat al werkt en behouden moet blijven
Bij de laatste browsertest zijn deze functies aangetoond:
- Afgeronde dossiers blijven inhoudelijk toegankelijk.
- Heropenen met een reden werkt.
- Gedeeltelijk crediteren en een fictieve terugbetaling werken.
- Na financiële afstemming kan het dossier opnieuw worden afgesloten.
- Klantgoedkeuring heeft afzonderlijke velden voor naam, datum en referentie.
- Een vaste offerteprijs kan zonder onnodig uurtarief naar een conceptfactuur.
Gebruik W106 en W109 als regressievoorbeelden. Verwijder hun historie niet. Maak nieuwe herkenbaar fictieve dossiers voor aanvullende tests.
1. Herstel tegenstrijdige statussen en vervolgacties
Geconstateerde problemen:
- Bij klanttegoed zegt de stappenhulp ‘Registreer fictieve betaling’, terwijl een terugbetaling nodig is.
- Na heropenen bleef bovenaan ‘administratief afgerond’ staan terwijl het dossier weer in behandeling was.
- Bij een definitieve factuur staat op sommige plekken nog ‘Conceptbedrag’.
Zorg voor één consistente statusweergave in dashboard, lijsten, dossierkop en stappenhulp. Onderscheid opdrachtstatus, factuurstatus, betalingsstatus en boekhoudstatus.
Laat de primaire vervolgactie aansluiten op de werkelijke situatie:
- Open saldo → betaling of opvolging.
- Klanttegoed → terugbetalen of expliciet verrekenen.
- Financieel verschil → afstemmen.
- Alles afgehandeld → afsluiten.
- Heropend dossier → zichtbaar opnieuw in behandeling.
Laat knoppen rechtstreeks het juiste formulier openen. Voorkom ongemerkte focusverplaatsing en overbodige dubbele klikken.
2. Maak betalingen volledig herstelbaar
Bied een begrijpelijke route voor:
- Een verkeerd ingevoerde betaling terugboeken met reden.
- Daarna de juiste betaling vastleggen.
- Ontbrekende betaalmethode of referentie aanvullen.
- Historische betalingen behandelen waarvoor onvoldoende brongegevens bestaan.
Bewaar oorspronkelijke registraties en correcties in de historie. Verzin ontbrekende gegevens niet. Maak onderscheid tussen het herstellen van metadata en het terugboeken van een bedrag.
Toon per registratie bedrag, datum, methode, referentie en correctiestatus. Controleer dat ontvangen bedragen, credits, terugbetalingen en openstaand saldo overal overeenkomen.
3. Maak het dossier sneller te begrijpen
Zet bovenaan een compacte samenvatting:
- Klant en werkzaamheden.
- Verantwoordelijke en planning.
- Huidige status en eerstvolgende actie.
- Prijsafspraak.
- Factuurbedrag inclusief en exclusief btw.
- Ontvangen, gecrediteerd, terugbetaald en resterend saldo.
Zet details daaronder in duidelijke onderdelen. Voorkom dat dezelfde factuurregels meerdere keren uitgebreid op dezelfde pagina staan.
Na afsluiten moet ik direct facturen, credits, betalingen, uitvoering en historie kunnen raadplegen. Gebruik begrijpelijk Nederlands, ook bij betaalmethoden.
4. Bewijs de dagelijkse materiaalroute
Test en herstel waar nodig:
Materiaalbehoefte → voorraad controleren → reserveren of inkopen → gedeeltelijk ontvangen → vervolg plannen → materiaal verbruiken → factureren.
Controleer dat:
- Voorraad nooit dubbel wordt afgeboekt.
- Gereserveerd materiaal niet als vrij beschikbaar verschijnt.
- Niet-gebruikt materiaal vrijgegeven kan worden.
- Retouren correct worden verwerkt.
- Materiaal bij een vaste offerteprijs niet dubbel wordt gefactureerd.
- De monteur deze handelingen vanuit zijn opdracht kan uitvoeren.
- De eigenaar ziet welke opdrachten vastlopen op levering.
5. Maak de boekhoudgrens controleerbaar
Behoud het onderscheid tussen export en echte verwerking.
Controleer of exportbestanden facturen, credits, betalingen en terugbetalingen onderling herleidbaar bevatten. Maak ontbrekende gegevens en noodzakelijke mappings zichtbaar.
Een download mag nooit automatisch ‘boekhoudkundig verwerkt’ betekenen. Toon een concrete status, bewijsreferentie en eventuele foutmelding.
Als geen boekhoudpakket beschikbaar is, test de lokale export op volledigheid en consistentie. Rapporteer externe importvalidatie als openstaand; simuleer geen bewezen koppeling.
6. Test gelijktijdig werken en herstel
Gebruik twee aparte browservensters om te controleren:
- Een opgeslagen wijziging verschijnt automatisch in het andere venster.
- Twee gebruikers die dezelfde gegevens wijzigen krijgen een begrijpelijke conflictmelding.
- Een conflict overschrijft geen wijzigingen ongemerkt.
- Dubbelklikken veroorzaakt geen dubbele betaling, credit of voorraadmutatie.
- Herladen behoudt opgeslagen gegevens.
- Een opslagfout wordt zichtbaar en laat invoer herstelbaar achter.
Als de beschikbare browseromgeving geen aparte vensters ondersteunt, vermeld dat expliciet. Presenteer een test met twee tabs niet als bewijs van twee vensters.
7. Valideer de hele klantreis opnieuw
Doorloop via de browser minimaal:
1. Directe opdracht zonder materiaal tot afsluiting.
2. Vaste offerte met materiaal en afwijkende werkelijke uren.
3. Offerte met afzonderlijk goedgekeurd meerwerk.
4. Onderdeel bestellen, gedeeltelijk ontvangen en vervolgbezoek.
5. Deelbetaling en restantbetaling.
6. Foutieve betaling terugboeken en correct opnieuw registreren.
7. Credit na volledige betaling, terugbetaling en opnieuw afsluiten.
8. Verlopen factuur met verantwoordelijke en opvolgdatum.
9. Winkelverkoop en retour met voorraadgevolgen.
Controleer bedragen, btw, voorraad, statussen, historie én gebruiksgemak. Voeg gerichte automatische tests toe voor financiële logica, statusovergangen, dubbele verwerking en conflicten. Controleer de schermen ook visueel.
Werkwijze
Onderzoek eerst de huidige code, projectinstructies en browserinterface. Maak zelfstandig redelijke implementatiekeuzes en werk door tot de afgesproken verbeteringen zijn uitgevoerd en gecontroleerd.
Gebruik uitsluitend fictieve gegevens. Verstuur geen echte berichten, bestellingen of betalingen en publiceer niets extern. Voeg geen knoppen toe die succes suggereren zonder bijbehorende werking.
Lever op
- De verbeterde applicatie.
- Een beknopt overzicht van wijzigingen.
- Testresultaten per scenario: geslaagd, geblokkeerd of niet getest.
- Screenshots als bewijs van belangrijke resultaten.
- Resterende beperkingen, duidelijk gescheiden van bewezen fouten.
- Een eerlijk oordeel als Henk: wat bespaart nu werk, wat blijft omslachtig en wat verhindert aanschaf?
Klaar betekent: ik kan als eigenaar en met mijn administratie normale opdrachten én financiële correcties zelfstandig afhandelen, zonder tegenstrijdige statussen, verborgen handwerk of onverklaarde bedragen. Externe functies die nog niet bewezen zijn, blijven herkenbaar openstaan.
