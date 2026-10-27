Mijn advies als Henk én ontwikkelaar: maak nu één complete, betrouwbare verkoopdemonstratie af. De basis is ver genoeg. De grootste winst zit in het herstellen van de gevonden fouten, aantonen dat de processen samen kloppen en duidelijk maken wat de klant koopt.
Geef Codex onderstaande opdracht:
Je bent een ervaren softwareontwikkelaar én Henk, eigenaar van een sleutelservice en winkel in hang- en sluitwerk en toegangscontrole.
Maak de bestaande Server4-demo zo ver mogelijk verkoopklaar. Voer de verbeteringen daadwerkelijk uit en test ze. Behoud bestaande gegevens, historie en werkende functies.
Verkoopklaar betekent: een ondernemer kan zelfstandig begrijpen wat het product oplevert, representatieve bedrijfsprocessen doorlopen en beoordelen wat hij krijgt. Maak eerlijk onderscheid tussen demonstratiefuncties en bewezen productiefunctionaliteit.
1. Herstel eerst de concrete fouten uit de praktijkproef
De laatste browsertest heeft aangetoond:
- Inkoop I2: vier artikelen, twee deelleveringen — voorraadberekening werkte.
- Verkoop B2: twee artikelen à €10 exclusief btw — €24,20 ontvangen.
- Eén retour — €12,10 terugbetaald en één artikel terug op voorraad.
- W113: twee artikelen verbruikt plus één uur arbeid — concept €80 exclusief, €96,80 inclusief btw.
- Financiële export en dashboard kwamen beide uit op €772,90 netto ontvangen.
Behoud deze uitkomsten als regressievoorbeelden.
Herstel:
- ‘Geef niet-gebruikt materiaal vrij’ reageerde niet zichtbaar. Laat deze actie het juiste formulier openen, de gekozen hoeveelheid vrijgeven en voorraad en reserveringen onmiddellijk bijwerken.
- Retourhistorie toont [object Object]. Toon artikel, hoeveelheid, datum, reden, bedrag, betaalmethode en verwijzing naar de oorspronkelijke verkoop.
- Opslagfeedback blijft achter. Geef na iedere actie een passende succes- of foutmelding. Verwijder oude meldingen die niet meer bij de laatste handeling horen.
- Onbekende factuurdatums in de export. Bewaar bij nieuwe definitieve facturen de juiste datum. Laat historische ontbrekende datums herkenbaar staan en bied gecontroleerde aanvulling met bron en historie.
Controleer ook gedeeltelijke vrijgave, gedeeltelijk materiaalretour en pogingen om meer vrij te geven of retourneren dan mogelijk.
2. Maak drie overtuigende klantreizen volledig af
Bouw geen losse demonstratieschermen. Gebruik de echte bestaande werkstromen met herkenbare fictieve gegevens.
A. De monteur
Klantvraag → offerte → akkoord → planning → materiaal reserveren → uitvoering → uren en materiaal → factuur → betaling → afsluiting.
B. Het ontbrekende onderdeel
Diagnose → onderdeelbehoefte → inkoop → gedeeltelijke ontvangst → open bestelrestant → klantopvolging → vervolgbezoek → uitvoering → facturatie.
C. De winkelbalie
Artikel zoeken → voorraad controleren → verkoop → betalingsregistratie → gedeeltelijke retour → terugbetaling → voorraad en administratie controleren.
Laat bij iedere reis zien wie aan zet is, wat de volgende stap is en welke gegevens automatisch meegaan. Laat de gebruiker terugkijken en fouten herstellen.
3. Bewijs financiële betrouwbaarheid
Controleer over alle schermen en exports:
- Vaste offerteprijs tegenover nacalculatie.
- Afzonderlijk goedgekeurd meerwerk.
- Materiaal zonder dubbele facturatie.
- Btw en afronding.
- Deelbetalingen.
- Terugboeking van een foutieve betaling.
- Credits en terugbetalingen.
- Open saldo en klanttegoed.
- Omzet tegenover netto ontvangen geld.
Maak bedragen herleidbaar naar de oorspronkelijke registraties. Voorkom dubbele verwerking door dubbelklikken, herladen of opnieuw aanbieden van dezelfde handeling.
Een definitieve factuur wordt gecorrigeerd via een herleidbare correctie, niet stilzwijgend overschreven.
4. Maak boekhoudverwerking concreet
Maak de export controleerbaar en documenteer:
- Welke gegevens volledig zijn.
- Welke gegevens ontbreken.
- Welke mappings nodig zijn.
- Hoe facturen, credits en geldmutaties aan elkaar gekoppeld zijn.
- Hoe totalen worden afgestemd.
Als een boekhoudpakket beschikbaar en geautoriseerd is, valideer een import in een testomgeving. Anders blijft externe import expliciet niet gevalideerd.
Gebruik nooit ‘boekhoudkundig verwerkt’ alleen omdat een bestand is gedownload of een gebruiker op een knop klikt zonder verwerkingsbewijs.
5. Test samenwerken en herstel
Controleer:
- Automatische synchronisatie tussen twee sessies.
- Conflicten wanneer dezelfde gegevens gelijktijdig worden gewijzigd.
- Geen ongemerkt verlies van wijzigingen.
- Begrijpelijke opslag- en verbindingsfouten.
- Gegevensbehoud na herladen.
- Een aantoonbare back-up- en herstelprocedure.
Test twee aparte browservensters wanneer de omgeving dat ondersteunt. Vermeld eerlijk welke omgeving is gebruikt en welke controles niet konden worden uitgevoerd.
Maak onderscheid tussen een rolkeuzeknop in de demo en echte toegangsbeveiliging. Doe geen productieclaims zonder bewijs.
6. Maak de demonstratie verkoopbaar zonder de werkplek te vervuilen
Voeg een afzonderlijk, compact onderdeel ‘Rondleiding’ toe met de drie klantreizen.
Per reis:
- Welke dagelijkse frustratie lost dit op?
- Welke medewerker gebruikt het?
- Wat hoeft niet opnieuw ingevoerd te worden?
- Wat is het aantoonbare eindresultaat?
Laat de rondleiding rechtstreeks bestaande dossiers en functies openen. Houd de gewone bedrijfswerkplek zelfstandig bruikbaar.
Toon tijdwinst alleen wanneer die gemeten is. Gebruik anders concrete aantallen vermeden handelingen, met een controleerbare toelichting. Verzin geen besparingspercentages.
Bied een veilige manier om uitsluitend de daarvoor aangemaakte demonstratiescenario’s opnieuw klaar te zetten. Wis geen bestaande gebruikers- of testhistorie.
7. Maak duidelijk wat de ondernemer koopt
Voeg een afzonderlijke pagina ‘Praktijkproef en aanschaf’ toe met:
- Voor wie het product geschikt is.
- Wat inbegrepen is en wat buiten de scope valt.
- Benodigde inrichting en gegevensimport.
- Beschikbare en nog ontbrekende koppelingen.
- Begeleiding bij overstappen.
- Ondersteuning en verantwoordelijkheden.
- Opslag, back-up, herstel en gegevensuitvoer.
- Een voorstel voor een afgebakende praktijkproef met meetbare succescriteria.
Verzin geen prijs, servicebelofte, beveiligingsgarantie of contractvoorwaarde. Gebruik uitsluitend bevestigde informatie. Markeer ontbrekende commerciële gegevens als ‘Nog vast te stellen’ en lever die apart als beslispunten voor de producteigenaar op.
8. Werk de gebruikerservaring af
Behoud het compacte dashboard. Controleer:
- Begrijpelijke taal.
- Consistente statussen en bedragen.
- Eén duidelijke primaire actie per stap.
- Rechtstreeks doorklikken naar de juiste gegevens.
- Goede leesbaarheid op laptop en smaller browserpaneel.
- Bediening met toetsenbord en zichtbare focus.
- Duidelijke lege toestanden en foutmeldingen.
- Geen technische objectnamen of ruwe data in gebruikersschermen.
Voeg geen extra dashboardkaarten toe tenzij ze een concrete beslissing ondersteunen.
Werkwijze
Werk in deze volgorde:
1. Gevonden fouten herstellen.
2. Drie klantreizen sluitend maken.
3. Financiële en voorraadcontroles uitvoeren.
4. Samenwerking en herstel toetsen.
5. Rondleiding en aanschafinformatie afwerken.
6. Eindcontrole vanuit Henk.
Gebruik uitsluitend fictieve gegevens. Verstuur geen echte berichten, bestellingen of betalingen. Publiceer niets extern.
Werk zelfstandig door binnen deze scope. Als externe toegang of commerciële informatie ontbreekt, rond het overige werk af en rapporteer de exacte openstaande afhankelijkheid.
Oplevering en acceptatie
Lever op:
- De werkende verbeterde demo.
- Browserbewijs van de drie klantreizen.
- Gerichte automatische tests voor risicovolle berekeningen en mutaties.
- Een overzicht met geslaagd, mislukt, geblokkeerd en niet getest.
- Screenshots van belangrijke eindresultaten.
- Een korte lijst van resterende aankoopbelemmeringen, gerangschikt op belang.
- Afzonderlijke oordelen over verkoopdemo gereed, praktijkproef gereed en productie gereed.
Het eindcriterium van Henk:
“Ik kan zien hoe dit mijn winkel, monteurs en administratie samen helpt. De bedragen en voorraad kloppen, fouten zijn herstelbaar en ik begrijp wat ik koop, wat het vraagt en welke beperkingen nog bestaan.”
Markeer de demo pas als verkoopklaar wanneer de drie klantreizen aantoonbaar werken en er geen bekende kritieke fouten verborgen blijven.
