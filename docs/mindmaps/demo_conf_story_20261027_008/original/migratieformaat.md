# Gecontroleerde fictieve proefmigratie

Account en praktijkproef → Vul fictief voorbeeld in → Voorvertoning controleren → Verwerk gecontroleerde proefimport. Iedere voorvertoning is gebonden aan de inhoudhash en administratierevisie. Een tussentijdse wijziging vereist een nieuwe controle. Fouten en mogelijke duplicaten blokkeren verwerking; geen gok op basis van overeenkomende namen.

JSON: vier verplichte velden `batch_id`, `customers`, `articles`, `balances`. Maximaal 1000 regels per sectie en 240 kB via het formulier. Elk bron-ID bestaat uit maximaal 60 letters/cijfers/_/-. Bedragen zijn gehele EUR-centen. Alleen 21% btw wordt ondersteund in deze demo. Gebruik uitsluitend fictieve gegevens.

```json
{"batch_id":"TEST_001","customers":[{"id":"K_TEST","name":"TEST klant (fictief)","address":"TEST Voorbeeldstraat 1"}],"articles":[{"id":"A_TEST","name":"TEST cilinder","unit_cents":1000,"vat_percent":21,"quantity":5,"location":"winkel"}],"balances":[{"id":"BEGIN_TEST","customer_id":"K_TEST","date":"2026-10-26","due":"2026-11-26","net_cents":10000,"vat_cents":2100}]}
```

Klanten en artikelen/prijzen staan in het geïmporteerde register, bereikbaar met Toon geïmporteerde stamgegevens. Beginvoorraad komt in de bestaande operationele voorraad. Reserveren zonder nieuwe prijs gebruikt een overeenkomende geïmporteerde artikelprijs en legt de importbron vast. Bestaande handmatige prijzen worden niet overschreven.

Beginsaldi zijn uitsluitend de RESTERENDE open vordering, met restantnetto en restant-btw uit gecontroleerde brondocumenten. Geen volledige historische factuur- of betalingsmigratie. Ze worden als afzonderlijke `opening_balance` geëxporteerd, tellen mee in debiteuren en niet in nieuwe omzet of oude ontvangsten. Controleer dat het oorspronkelijke factuurnummer niet al bestaat. Negatieve saldi, meerdere valuta of andere btw-tarieven blijven geblokkeerd en vereisen uitbreiding.

Bron-ID, naam, voorraadlocatie en factuurnummer worden op mogelijke dubbelen gecontroleerd. Hetzelfde batch-ID met dezelfde inhoud verandert aantallen/saldi niet opnieuw; hetzelfde batch-ID met andere inhoud wordt geweigerd. Een nieuwe batch met reeds gebruikte bron-ID’s wordt geblokkeerd. Een eventuele lege herhaalaanvraag kan wel als herleidbare opslagactie in de algemene historie verschijnen; er ontstaat geen tweede importregistratie.

Voer een proef eerst geïsoleerd uit, vergelijk aantallen, som beginvoorraad en totale beginsaldi met de bron en de importhistorie, controleer financiële afstemming en maak een herstelpunt vóór een eventuele geautoriseerde echte migratie. Echte migratie/toestemming, mapping en cutover zijn nog niet afgesproken.
