# Back-upbeslissing en lokaal herstel

**Externe back-up: nog niet ingericht en getest.** Er is geen door de producteigenaar gekozen en geautoriseerde externe bestemming in gebruik. Gebruik nog geen externe dienst of opslag. De oorspronkelijke Server5-backuptaak is ongewijzigd actief; er is geen automatische Server4-overdracht meer aan gekoppeld.

## Voorbereid, maar niet actief

backup-config.example.json bevat een niet-actief configuratievoorbeeld met lege bestemming, toestemming, verantwoordelijke, frequentie, retentie, encryptie/sleutelbewaring en hersteldoelen. De producteigenaar kiest eerst opslag buiten de Server4-host en bevestigt gebruik. Een keuze in het proefvoorstel is een herleidbare beslissing, geen bewijs dat er al een externe kopie is gemaakt of hersteld.

recovery.py kan bij een later expliciet gekozen/geautoriseerde gemounte bestemming kopiëren met `--external-destination /EXPLICIET_GEKOZEN_MOUNT`. Het pad is instelbaar en een kopie op hetzelfde filesystem wordt geweigerd. Een ander filesystem bewijst op zichzelf niet dat opslag buiten Server4 staat; laat herkomst/mount, rechten, encryptie, sleutelbewaring en eigenaarschap eerst beoordelen. Er is geen vooringevuld pad, extern account, API of cloudleverancier. Het voorbeeldbestand activeert niets.

## Lokale back-up en geïsoleerde hersteltest

Maak op Server4 een lokale snapshot met `.venv/bin/python recovery.py`. De snapshot bevat de applicatiebron, workflow en tegelconfig, appaccounts en sessiesleutel, en een controlemanifest. De workflow wordt als één atomisch opgeslagen bedrijfstoestand gelezen, de authdatabase met SQLite online backup. Een bronwijziging tijdens kopiëren wordt geweigerd. Behandel de snapshot als vertrouwelijk; neem nooit SSH-/Codex-authbestanden mee.

Herstel eerst naar aparte lege app-/statemappen, niet over de draaiende demo. recovery.restore valideert paden/checksums vóór schrijven, bewaart eerst aanwezige nieuwere doeldata en trekt teruggezette browser-sessies in. Vergelijk workflow byte voor byte (dossiers, historie, voorraad, reserveringen, facturen, credits, betalingen), accountaantallen, exporthash en financiële controletotalen. Een gewijzigde backup moet vóór schrijven worden geweigerd. Leg resultaat en beperkingen vast.

Voor live gegevensherstel: bestaande dienst stoppen, snapshot en nieuwere historie vergelijken en een aparte herstelbeslissing nemen. Overschrijf nooit nieuwere bedrijfsgegevens op basis van alleen een geslaagde test. Geen live restore uitgevoerd.

## Afzonderlijke beslissing vóór echt bedrijfsgebruik

De producteigenaar kiest bestemming buiten Server4, budget, eigenaar/toestemming, toegangsrechten, frequentie, retentie, encryptie/sleutelbewaring en hersteldoelen. Configureer en test daarna de echte externe kopie én herstel vanaf die bestemming. Tot die tijd blijft de externe status hierboven open.

Historische technische proef: vóór de nadere eigenaarinstructie is Server5 tijdelijk als proefbestemming gebruikt. De automatische koppeling is daarna teruggedraaid; proefartefacten zijn afgeschermd behouden en tellen niet als een gekozen/ingeregelde externe voorziening. Zie het lokale opleverrapport voor dit onderscheid. De demo toont deze oude proef niet als actuele externe levering.
