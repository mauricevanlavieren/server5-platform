# Concept begeleide fictieve praktijkproef — 27 oktober 2026

Doel: vaststellen of een monteur, winkelmedewerker en administrateur hun relevante werk zelfstandig kunnen uitvoeren, de bedragen/voorraad sluiten en herstel van een andere host lukt. Geen nieuwe dashboardfuncties. Geen overeengekomen aanbod, prijs, looptijd of supportcontract.

## Voorbereiding en afbakening

- Producteigenaar kiest proefperiode, begeleider/aanspreekpunt en drie deelnemers.
- Leg vóór start inrichting/periodieke kosten of expliciete kosteloze-proefafspraak vast; het systeem neemt kosteloosheid niet aan.
- Alleen fictieve klanten, opdrachten, artikelen, prijzen, betalingen en bronbestanden.
- Persoonlijke proefaccounts met eigenaar-, monteur-, winkel- en administratierechten. Gedeelde demo blijft beschikbaar maar telt niet als medewerkersidentificatie.
- Eigenaar legt werktijden, toewijzingen, bronprijzen en beginvoorraad vast. Geen ondersteuningstijden of SLA verzonnen.

## Uitvoering en acceptatie

1. Monteur vindt eigen toegewezen dossier, registreert bevindingen/uren/materiaal, verwerkt reserveringen, meldt gereed en controleert behoud na herladen.
2. Winkel controleert vrije voorraad en prijsbron, verkoopt fictief contant, verwerkt een gedeeltelijke retour met reden/datum en controleert voorraad, terugbetaling en historie.
3. Administratie controleert overgenomen werk/prijsbronnen, maakt de factuur definitief, registreert fictieve betaling, controleert debiteur/afsluiting en stemt export af.
4. Iedere deelnemer legt zelf geslaagd/mislukt/geblokkeerd, beoordeelde stappen, benodigde hulp en concrete bevindingen vast. Dit is een eigen verklaring, geen onafhankelijke certificering. Een demo-actor telt niet mee als echte medewerkersacceptatie.
5. Test twee sessies en een conflict/herhaalde aanvraag; behoud invoer en geen dubbele mutaties. Technische browserproeven worden apart gerapporteerd.
6. Controleer back-up op aparte host en herstel die geïsoleerd; vergelijk alle dossiers/historie/voorraad/reserveringen/facturen/credits/betalingen en controletotalen.
7. Kies doelboekhoudpakket/testadministratie/mappings en voer één geautoriseerde fictieve proefimport uit. Lees uit het doelpakket aantallen, btw, omzet na credits, debiteuren, betalingen en relaties terug. Zolang die toegang ontbreekt: externe import niet gevalideerd.

## Boekhoudhandwerk zichtbaar maken

De boekhoudvoorbereiding toont exportaantallen, documentsoorten en historische bronproblemen. Resterend werk: bronvelden met bewijs aanvullen; debiteuren matchen; dagboek/grootboek/btw-codes kiezen; doelformaat/tekens/bedragen bepalen; documenten en credits/betalingen koppelen; doelpakket teruglezen en verschillen onderzoeken. Meet benodigde hulp, velden en minuten tijdens de proef. Een download, interne vergelijking of eigen bevestiging geldt niet als bewijs van externe verwerking.

## Levering, ondersteuning en uitstap

Eigenaarsformulier op /proefvoorstel bewaart periode, contact, prijs, inbegrepen/uitgesloten functies, migratie/training, support, bereikbaarheid/storingsafhandeling, hosting, backupbeleid/hersteldoelen, looptijd/opzegging en gegevensuitvoer met bron/akkoordreferentie en wijzigingshistorie. Lege keuzes blijven Nog vast te stellen. Eigenaarinvoer bewijst niet automatisch instemming van een externe leverancier.

Externe back-up: nog niet ingericht en getest. De producteigenaar kiest eerst een bestemming buiten Server4 en geeft afzonderlijk toestemming voor gebruik. Een instelbare kopie en lokale herstelprocedure zijn voorbereid. Gebruik nog geen externe dienst/opslag. Ondersteuning: contactpersoon, contactgegevens, bereikbaarheid en responstijd zijn nog vast te stellen. Beide punten zijn beslissingen vóór echt bedrijfsgebruik.

## Evaluatiebesluit

Geslaagd wanneer de drie deelnemers de route zelfstandig afronden, voorraad/geld exact sluiten, fouten herkenbaar/herstelbaar zijn en het resterende boekhoudwerk en de leveringsvoorwaarden concreet zijn. Bij fouten: oorzaak/maatregel/volgende proef vastleggen. Besluit apart over verkoopdemo, verdere fictieve proef, echte gegevens en productie. Externe boekhoudimport, commerciële overeenkomst en feitelijke medewerkersacceptatie blijven open totdat hun bewijs/keuzes beschikbaar zijn.

De boekhoudadapter staat los van de bedrijfsregels: accounting.py verwerkt een pakketneutrale read-only momentopname uit data.accounting_snapshot(). Nog geen pakket gekozen. Vraag de producteigenaar welk pakket de eerste beoogde klant gebruikt en of daarvoor een geautoriseerde testomgeving beschikbaar is. Valideer vervolgens die ene koppeling volledig voordat meerdere pakketten worden ondersteund.
