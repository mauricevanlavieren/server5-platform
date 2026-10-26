# Henk-demo — praktijkproefronde 2, 26 oktober 2026

**Resultaat: uitgevoerd en getest.** Opdracht uit de bijgewerkte `/home/mau/demo-conf.md`, lokaal bewaard als requirements.md. Taak `demo_conf_review_20261026_002`. Bestaande applicatie op Server4 aangepast via de bestaande SSH-route vanaf geverifieerde Server5. Concrete eigenaaropdracht autoriseert deze Server4-demo; geen andere hosts aangepast. Bestaande vuile Server5-werkboom behouden. Geen echte berichten, bestellingen, betalingen of externe publicaties. Geen Notion-mutatie: “publiceer niets extern” uit de huidige opdracht gaat vóór de algemene snapshotafspraak. Lokale Current Projects-kaart wel bijgewerkt.

## Onderzoek, wijzigingen en reden

Code, projectinstructies, huidige workflowdata en de daadwerkelijke browserinterface onderzocht. De vorige functies bleven behouden: dossiers na afsluiting, heropenen met reden, credits/refunds, afzonderlijke goedkeuringsvelden en vaste-prijsconcepten zonder uurtarief. W106 is in de uitgangstoestand afgesloten met correcties; W109 heeft een vaste-prijsconcept. Beide zijn regressievoorbeelden, hun opgeslagen inhoud/historie is niet gewijzigd. Original/ bevat de bron vóór deze ronde; before-W109.png toont de uitgangsinterface.

1. **Eén statusafleiding.** `dossier_state` onderscheidt opdracht, factuur, betaling en boekhouding. Dashboard/lijsten/dossierkop gebruiken dezelfde afleiding. Heropenen toont ‘Opnieuw in behandeling’. Klanttegoed leidt naar terugbetaling, positief saldo naar betaling, registratieverschillen naar afstemming en nulsaldo naar afsluiten. Een boekhoudfout blokkeert afsluiten totdat die expliciet met bewijsreferentie is afgehandeld. De stappenhulp opent het juiste formulier, niet een onzichtbare volgende knop. Definitieve facturen krijgen het label Factuurbedrag; Conceptbedrag blijft voor concepten.
2. **Betalingen herstellen.** Een historische betaling zonder nummer krijgt een stabiele interne verwijzing in de weergave, zonder een migratie van de live opslag. Vanuit die verwijzing kun je terugboeken of uitsluitend metadata aanpassen. Datum, methode en referentie zijn apart; Nederlandse labels Bank/Kas/Pin/Onbekend. Bij metadata blijven bedrag en oorspronkelijke registratie behouden, met voor/na-historie, actor, tijd en reden. Alleen aantoonbare bronnen mogen als aangetoond worden gemarkeerd; onbekende waarden blijven leeg en expliciet onzeker. Terugboeken van een bedrag is een andere actie. Ook na een refund kan een oorspronkelijke foutieve betaling worden teruggeboekt en correct opnieuw ingevoerd; het nieuwe saldo moet weer worden afgehandeld.
3. **Dossier sneller begrijpen.** Bovenaan staan klant/werk, verantwoordelijke/planning, vier statussen, volgende actie, prijsafspraak, excl./incl. btw, ontvangen/credit/refund/open. De samenvatting blijft bovenaan bij gereed of gesloten werk. Dubbel uitgewerkte factuurregels bij prijscontrole verwijderd; regels, uitvoering, correcties en historie zijn apart raadpleegbaar. Na afsluiten blijven die direct beschikbaar. Belangrijke historieacties en betaalmethoden hebben Nederlandse labels.
4. **Materiaalroute.** Behoefte, vrije voorraad, reservering, inkoop/deelontvangst, vervolgplanning, verbruik en factuur zijn opnieuw getest. De stappenhulp volgt nu de echte inkoop-/ontvangst-/vervolgstap. Gereedmelden terwijl levering of vervolgplanning nog openstaat is geblokkeerd; diagnose als concept opslaan blijft mogelijk. Reservering telt niet als vrij, verbruik/retour gebeurt eenmaal en een vaste offerteprijs telt materiaal niet dubbel.
5. **Controleerbare export.** Canonieke CSV bevat facturen, credits, betalingen, terugboekingen, refunds, metadatacorrecties, winkelverkopen/-ontvangsten/-retouren/-refunds. Elke correctie verwijst naar de factuur of verkoop; metadatacorrecties/terugboekingen bovendien naar de oorspronkelijke betaling. Bronhashes, ontbrekende velden en vereiste mappings staan expliciet in het bestand. Downloaden wijzigt geen boekhoudstatus. Export, handmatige bevestiging met bewijs en afstemmingsfout blijven gescheiden.
6. **Herstel bij fouten en dubbelklikken.** Elke nieuwe interfaceaanvraag heeft een uniek nummer. Een persistent ontvangstbewijs met payloadhash voorkomt herhaalde mutaties na een verloren antwoord, ook na een revisiewijziging. Een ander bedrag onder hetzelfde nummer wordt geweigerd. Revisies blijven conflicten tegenhouden. Opslagfouten geven HTTP503 met duidelijke melding; invoer blijft staan. Metadata- en heropenvelden worden ook als onopgeslagen invoer beschermd. Navigatie waarschuwt bij onopgeslagen dossierinvoer.

## Browserresultaten per gevraagde route

Echte Chromium, zichtbare knoppen en formulieren. Muterende proeven uitsluitend in een afzonderlijke kopie op Server5 (`serve-test.py`, 127.0.0.1:8878). API-GETs dienen voor bedrag/statusasserties. Nieuwe testdossiers hebben herkenbare fictieve namen. Geen live gebruikersdata gereset of gemuteerd.

| # | Gevraagd scenario | Resultaat / controle |
|---|---|---|
| 1 | Directe opdracht zonder materiaal tot afsluiting | **Geslaagd** — klantakkoord, planning, uitvoering, €60 excl./€72,60 incl., fictieve betaling en afsluiting. dossier-afgerond.png |
| 2 | Vaste offerte met materiaal en afwijkende uren | **Geslaagd** — €100 excl. afspraak, 2 werkelijke uren en €25 materiaalverbruik; factuur blijft €100 excl./€121 incl., één vaste-prijsregel. vaste-prijs.png |
| 3 | Offerte plus afzonderlijk goedgekeurd meerwerk | **Geslaagd** — €100 + €25 = €125 excl., aparte regels en goedkeuring met naam/datum/referentie. |
| 4 | Bestellen, deelontvangst en vervolgbezoek | **Geslaagd** — ontvangst 1+1 op bestelling 2, verbruik 1, diagnose 0,5u + vervolg 1u, €15 materiaal, concept €105 excl. Nieuwe guard-/stappenhulpwijziging afzonderlijk opnieuw getest. onderdelen-en-bezoeken.png |
| 5 | Deelbetaling en restant | **Geslaagd** — €20 op €72,60, €52,60 resterend, daarna nulsaldo. |
| 6 | Verkeerde betaling terugboeken en correct invoeren | **Geslaagd** — oude ontvangst met terugboekreden behouden, saldo heropent, correcte €52,60 opnieuw ingevoerd, saldo terug nul. |
| 7 | Credit na volledig betaald, terugbetaling en opnieuw afsluiten | **Geslaagd** — €10,01 + €2,10 btw levert €12,11 tegoed; juiste terugbetaalroute. Aanvullend bestaand nieuw TEST-dossier W116 heropend, extra €5 + €1,05 credit, €6,05 terugbetaald en opnieuw gesloten; historie behouden. opnieuw-afgesloten-na-credit.png |
| 8 | Verlopen factuur met actor en opvolgdatum | **Geslaagd** — F103, verantwoordelijke Lina, 28 oktober, interne notitie; geen echte verzending. |
| 9 | Winkelverkoop en retour | **Geslaagd** — voorraad 3 → verkoop 2 → 1 → retour 1 → 2; refund €12,11 incl. btw, gekoppelde financiële/voorraadgevolgen. |

Bewijs: browser-tests.cjs / browser-results.json (alle tien bestaande routes, waarvan 1–9 hierboven); browser-parts.cjs / browser-parts-results.json voor de laatste materiaalwijziging; browser-reclose.cjs / browser-reclose-results.json voor heropenen en opnieuw afsluiten; browser-additional.cjs / browser-additional-results.json voor volledige credit, refund, vervangende factuur en exportstatus. Geen browserfouten in de geslaagde resultaten.

## Twee vensters, metadata en foutafhandeling

**Afzonderlijke vensters daadwerkelijk ondersteund en getest.** Headed Chromium onder Xvfb, twee geïsoleerde browsercontexten met normale vensters. CDP bevestigt verschillende windowIds in browser-window-identities.json. Dit is een virtueel beeldscherm, geen claim van een fysieke telefoon- of desktopgebruikersproef. Geen tabtest als vensterbewijs gepresenteerd.

browser-recovery.cjs / browser-recovery-results.json bewijzen:

- Metadata van een historische betaling aanvullen zonder wijziging van bedrag/aantal; origineel en reden blijven zichtbaar. Screenshot betaalgegevens-en-historie.png.
- Twee vensters: eerste eigen invoer blijft staan na opslag in het tweede; stale save geeft conflict, expliciet ophalen werkt, schone versie synchroniseert automatisch en herladen behoudt de opgeslagen gegevens. Screenshots eerste-venster-conflict.png en tweede-venster-opgeslagen.png.
- Gecontroleerd geïnjecteerde HTTP503: zichtbare fout, invoer behouden en niets opgeslagen. Daarna herstel en dubbelklik: één betaling.
- Antwoordverlies ná echte opslag: interface houdt invoer, opnieuw proberen onder hetzelfde aanvraagnummer maakt geen tweede betaling.
- Werkelijke dubbele klik op credit en voorraadontvangst: één credit en één voorraadmutatie.

De HTTP503 en verloren netwerkrespons zijn bewust geïnjecteerde foutproeven. status-tests.py test daarnaast een daadwerkelijke `os.replace`-fout in tijdelijke opslag: oude bytes blijven intact en retry verwerkt eenmaal. Dit is geen claim dat een echte schijfstoring op de live host heeft plaatsgevonden.

## Automatische controles en export

status-results.json: legacy metadata, onbekende bron, consistente heropenstatus, credit → refund, opnieuw sluiten, terugboeken en herbetalen na refund, aanvraagreplay, echte tijdelijke opslagfout, exportrelaties/mappings, W106/W109-identiteit en onderdeelstappen/gereedmeldblokkade.

financial-results.json: financiële berekeningen, cumulatieve btw, saldo/ledger bij vervanging, negatieve invoer, overbetaling, revisies, terugboekduplicaten, vrijgeven/retour, inkoopontvangst, annulering/garantie en behoud regressiedossiers. recovery-results.txt: backup, gecontroleerd herstel met behoud van actuele toestand en weigering bij beschadigd manifest, uitsluitend tijdelijke data. Python compile en JavaScript syntaxcontrole geslaagd.

export-check.py / export-results.json / export-sample.csv: **48 gekoppelde regels** uit de uiteindelijke testadministratie. IDs uniek, alle ouders aanwezig, betalingen/terugboekingen/refunds sluiten per factuur aan, credits kloppen, omzet en netto-ontvangsten zijn gelijk aan dashboard en ontbrekende gegevens/mappings zijn zichtbaar. Download verandert geen opslagbytes of verwerkingsstatus. Het bestand bevat nadrukkelijk fictieve testadministratie. **Externe importvalidatie: niet getest/openstaand**; geen beschikbaar boekhoudpakket of bewezen koppeling geclaimd. Voorbereidingsdoel blijft e-Boekhouden.nl, met handmatige mapping/proefimport volgens README.

## Live oplevering, regressie en rollback

Server4 `/home/mau/server4-mobile-demo`: gewijzigd app.py, business.py, workflow.py, data.py, improvements.py, static/app.js, static/style.css en README.md. recovery.py en static/index.html ongewijzigd meegeverifieerd. Bestaande userdienst herstart, geen nieuwe permanente service, netwerkinstellingen of authenticatie gewijzigd. Geen nieuwe installatie nodig; bestaande Chromium/Playwright/Xvfb hergebruikt. Geen rootwebservice, reboot of securityprofielwijziging.

deployment-results.json: health en zes applicatieroutes HTTP200; geleverde assets gelijk aan bron. Workflow vóór/na byte-identiek, SHA256 `e81cedfe85867f9ef41edb26df36df43dc6aae808095b48979e1d4f2141eba79`. Alle bestaande dossiers, credits, betalingen, materialen en histories behouden, inclusief W106 en W109. Bestaande omzet €1020 excl. btw en open €473,40 incl. btw behouden. De nieuwe statusweergave voegt alleen afgeleide informatie toe aan de API, niet aan opgeslagen dossiers.

Read-only live Chromium-proef via tijdelijke SSH-loopbackforward: live-browser-results.json. Screenshots live-dashboard.png, live-W106.png, live-W109.png en live-mobiel-W109.png. Bestaande afgesloten W106 is inhoudelijk toegankelijk; W109 blijft dezelfde vaste-prijsconceptfactuur. Desktop en 390px mobiele viewport visueel gecontroleerd, geen horizontale paginaoverflow. Dit bewijst lokale HTTP via private SSH, geen nieuwe private HTTPS-, fysieke telefoon- of microfoonacceptatie.

Backup vóór deze ronde: Server4 `backups/demo_conf_review_20261026_002/`, met originele bronnen, workflowreferentie en tegelconfig. Eindcorrectie-backup: `backups/demo_conf_review_20261026_002-final/`. Laatste volledige bron+databackup en manifest staan onder new_snapshot in deployment-results.json. Geen credentials opgenomen. Bestaande monitoring/backups niet vervangen; nieuwe aanvraagontvangstbewijzen en metadatahistorie zitten in dezelfde workflow.json en vallen mee in recovery.py.

Rollback: controleer latere wijzigingen, stop bestaande userdienst, herstel uitsluitend de genoemde bronbestanden met hun relatieve paden uit de **eerste** backup van deze ronde, start dienst en controleer health/bedragen/dossiers. Geen datarestore nodig voor bronrollback; nieuwe velden zijn additief. Zet workflow-reference.json nooit blind terug over nieuwere gebruikerswijzigingen. Voor bewust gegevensherstel: README/recovery.py met geverifieerd manifest en automatische before-restore-backup; geen live datarestore uitgevoerd.

## Henk-oordeel en grenzen

**Praktijkproef: ja, gecontroleerd met fictieve gegevens.** Werkbesparing: één registratie voor uitvoering/factuur, direct saldo en verantwoordelijke zichtbaar, herstel zonder historie opnieuw opbouwen, historische betaalgegevens aanvullen zonder bedragtrucs, en materiaalketen vanuit dezelfde opdracht. Krediet, terugbetaling en herafsluiting zijn nu zelfstandig uitvoerbaar met verklaarbare bedragen.

**Wat nog omslachtig blijft:** uitzonderingen en broncontrole vragen bewuste invoer; lange dossiers hebben nog meerdere uitklaponderdelen; boekhoudmapping/import is handwerk. Onvoldoende brongegevens blijven als onzekerheid staan. Een echt onverklaard verschil tussen totaalsaldo en bronregistraties blokkeert afsluiten en vereist oorspronkelijke bewijsstukken; de app verzint geen oplossing.

**Aanschaf/productie: nog niet.** Open beperkingen zijn echte gebruikersaccounts/rechten, gevalideerde externe boekhoudimport, bank/mail/leverancierskoppelingen, stamgegevens en kostprijsadministratie, operationele externe backup en fiscale/productiebeoordeling. Eén JSON-opslag en één schrijfproces blijven de demogrens. Rollen zijn presentatie, geen toegangsbeveiliging. Externe handelingen blijven lokale fictieve registraties. De bestaande fysieke telefoon-/spraakacceptatie blijft een afzonderlijke open taak. Deze beperkingen zijn geen verborgen succeslabels. De concreet gevonden status-, metadataroute-, dubbelverwerkings- en materiaalstappenfouten uit deze ronde zijn hersteld en getest; er wordt geen algemene bugvrijheid geclaimd.

## Taakstatus

Succeeded voor deze opdracht. Current Projects: 4 vóór → 6 tijdens → 4 na; eigen uitvoeringsblad en taakwortel gesnoeid met bewijs, bestaande telefoonblokkade behouden. during-validation.json/final-validation.json bewijzen consistent=true, gelijke bron/publicatiehash en project_invariants_valid=true; iedere done-node is een blad. CLI-taak zonder brokerrecord; geen brokerresultaat vervalst. Volgende gebruikersstap: demo herladen en de nieuwe samenvatting en betaalcorrecties uitproberen met fictieve gegevens. Geen extern gepubliceerd werklog.
