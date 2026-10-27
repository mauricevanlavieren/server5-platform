Als Henk: nog niet voor dagelijks bedrijfsgebruik. Wel zou ik een begeleide praktijkproef willen starten.
Ik heb de aanschafpagina opnieuw geladen en gecontroleerd. De doorslaggevende koopvoorwaarden staan nog steeds open:
Wat mij tegenhoudt	Wat nodig is voor mijn ‘ja’
Prijs en contract zijn onbekend	Concreet aanbod: inrichting, maandkosten, inbegrepen functies en opzegging
Ondersteuning is niet afgesproken	Een aanspreekpunt, bereikbaarheid en afspraken bij storingen
Accounts en rechten zijn niet aangetoond	Bewijs dat monteur, administratie en eigenaar uitsluitend passende toegang hebben
Boekhoudimport is niet gevalideerd	Eén geslaagde proefimport met aansluitende facturen, credits en betalingen
Back-up staat volgens de pagina op dezelfde host	Een externe kopie en aantoonbaar geslaagde hersteltest
Overstappen is nog niet uitgewerkt	Een gecontroleerd migratieplan voor klanten, artikelen, voorraad en beginsaldi


De eerder geteste werkprocessen geven mij voldoende vertrouwen om verder te onderzoeken. Mijn belangrijkste bezwaar is inmiddels: kan ik mijn bedrijf hier verantwoord van afhankelijk maken, en tegen welke kosten?
Deze ronde heb ik de actuele aanschafinformatie gecontroleerd; ik heb geen volledige klantreis opnieuw uitgevoerd. Als de technische voorzieningen inmiddels gebouwd zijn, moet de demo daarvan bewijs tonen en de aanschafpagina worden bijgewerkt.
Mijn advies: laat Codex de technische voorwaarden aantonen. Vul daarnaast zelf het commerciële aanbod en de ondersteuningsafspraken in. Een volgende visuele verbetering alleen verandert mijn koopbesluit niet.


14:11







zou je codex weer een software developer opdracht willen geven







14:12






Kopieer onderstaande opdracht naar Codex:
Maak de bestaande Server4-applicatie aantoonbaar gereed voor een begeleide praktijkproef. Richt deze ronde op de resterende aankoopbezwaren, niet op extra dashboardfuncties.
Onderzoek eerst de huidige code, projectinstructies en implementatie. Behoud bestaande gegevens, historie en werkende functies. Implementeer ontbrekende onderdelen en test ze daadwerkelijk.
1. Onderzoek het verschil tussen implementatie en productinformatie
De aanschafpagina vermeldt momenteel dat accounts, toegangsrechten, externe verwerking en productieafspraken niet zijn aangetoond.
Maak een overzicht per onderwerp:
- Wat bestaat daadwerkelijk?
- Welk bewijs is beschikbaar?
- Wat ontbreekt?
- Welke externe toegang of beslissing is nodig?
Werk verouderde informatie bij op basis van bewijs. Verwijder beperkingen niet alleen om de demo overtuigender te laten lijken.
2. Implementeer en test echte toegang
Gebruik passende, onderhouden authenticatiecomponenten en controleer autorisatie aan de serverzijde.
Minimale rollen:
- Eigenaar: instellingen, tarieven, gebruikers en financiële correcties.
- Monteur: toegewezen opdrachten, uitvoering, uren en materiaal.
- Administratie: facturen, betalingen, debiteuren en export.
Test minimaal:
- Niet-ingelogde toegang wordt geweigerd.
- Een monteur kan ook via directe verzoeken geen betalingen, tarieven of gebruikersrechten wijzigen.
- Sessies kunnen worden beëindigd.
- Belangrijke mutaties zijn herleidbaar naar een gebruiker.
Behoud een eventuele demonstratiemodus, maar onderscheid die duidelijk van echte gebruikersbeveiliging.
3. Bewijs back-up en herstel
Maak een consistente back-up en herstel die in een geïsoleerde omgeving.
Vergelijk vóór en na herstel:
- Dossiers en historie.
- Voorraad en reserveringen.
- Facturen, credits en betalingen.
- Financiële controletotalen.
Documenteer de procedure en het resultaat. Bereid een externe back-upbestemming voor, maar verzin geen werkende externe opslag wanneer die niet beschikbaar is. Verwijder geen bestaande gegevens tijdens de hersteltest.
4. Maak boekhoudafstemming controleerbaar
Controleer de export op bedrijfsdatums, documentnummers, btw, bedragen en onderlinge verwijzingen.
Voeg een controle toe die verschillen rapporteert tussen:
- Definitieve omzet na credits.
- Openstaande debiteuren.
- Netto ontvangen geld.
- De onderliggende exportregistraties.
Valideer een proefimport wanneer een geautoriseerde boekhoudtestomgeving beschikbaar is. Anders blijft ‘externe import niet gevalideerd’ expliciet openstaan.
Een download of handmatige bevestiging geldt niet zelfstandig als bewijs van externe verwerking.
5. Maak overstappen uitvoerbaar
Bied een gecontroleerde proefimport voor klanten, artikelen, prijzen, beginvoorraad en openstaande saldi.
Vereisten:
- Voorvertoning vóór definitief verwerken.
- Validatiefouten per regel.
- Detectie van mogelijke duplicaten.
- Geen dubbele verwerking bij herhalen.
- Afstemming van aantallen en beginsaldi.
- Herleidbare importhistorie.
Gebruik fictieve bronbestanden en documenteer het benodigde formaat.
6. Verifieer de dagelijkse werking
Doorloop de drie bestaande klantreizen volledig:
1. Offerte → uitvoering → factuur → betaling → afsluiting.
2. Onderdeelbehoefte → inkoop → deellevering → vervolgbezoek.
3. Winkelverkoop → gedeeltelijke retour → terugbetaling.
Test tevens twee gelijktijdige sessies, wijzigingsconflicten, dubbelklikken en gegevensbehoud na herladen.
Controleer de datumlogica: bedrijfsdatum en werkelijk registratietijdstip moeten afzonderlijk en consequent worden gebruikt.
7. Maak commerciële keuzes gericht invulbaar
Lever een afzonderlijk beslisoverzicht voor de producteigenaar op met:
- Eenmalige inrichting en periodieke prijs.
- Inbegrepen functies en koppelingen.
- Migratie en training.
- Ondersteuning, onderhoud en storingsafhandeling.
- Hosting, back-up en verantwoordelijkheden.
- Looptijd, opzegging en gegevensuitvoer.
Verzin deze afspraken niet. Verwerk uitsluitend bevestigde informatie op de aanschafpagina. Ontbrekende keuzes blijven zichtbaar als openstaande beslispunten.
Werkwijze en grenzen
Gebruik uitsluitend fictieve gegevens. Verstuur geen echte berichten, bestellingen of betalingen. Publiceer niets extern en verruim geen toegang tot de applicatie zonder afzonderlijke toestemming.
Rond onafhankelijk uitvoerbaar werk af wanneer externe toegang ontbreekt. Rapporteer daarna precies wat nog nodig is.
Oplevering
Lever op:
- De werkende wijzigingen.
- Gerichte automatische tests voor rechten, berekeningen, imports en dubbele verwerking.
- Browserresultaten per scenario: geslaagd, mislukt, geblokkeerd of niet getest.
- Bewijs van herstel en financiële afstemming.
- Bijgewerkte aanschafinformatie.
- Resterende technische én commerciële aankoopbelemmeringen.
Geef afzonderlijk een oordeel over verkoopdemo, begeleide praktijkproef en productiegebruik.
Acceptatiecriterium van Henk:
“Mijn medewerkers kunnen hun werk zelfstandig doen, bedragen en voorraad sluiten aan, fouten en uitval zijn herstelbaar, en ik weet wat ik krijg en wie mij ondersteunt. Wat nog niet bewezen is, wordt duidelijk vermeld.”
