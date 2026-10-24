# server5-commandcenter — actuele uitvoeringsafspraak

Volg /home/mau/AGENTS.md. Server5 is een experimentele speeltuin; mobiele MVP-implementatie en lokale sudo/rootacties zijn geautoriseerd. Bubblewrap/AppArmor is niet langer een releasevoorwaarde en wordt niet verder onderzocht. Geen externe systemen wijzigen, geen publieke interface, geen secrets in Git/Notion, geen onomkeerbare vernietiging zonder toestemming. Actuele architectuur/runbook: docs/mvp-runbook.md zodra aangemaakt; oudere M0/planning-only-afspraken zijn historisch en vervangen.

## Verplicht bij IEDERE Codex-opdracht — Current Projects lifecycle

Deze uitvoeringsafspraak geldt ook voor gewone web-/CLI-opdrachten zonder
`[CURRENT PROJECTS]`-prefix. Lees haar vóór uitvoering; werk uitsluitend op Server5.
Geen nieuwe service, scheduler, monitoring of automatisch vervolgproces hiervoor.

1. Registreer vóór uitvoeringswijzigingen de unieke broker-taak-ID uit
   `SERVER5_TASK_ID` (CLI zonder broker: genereer één stabiele unieke taak-ID).
   Lees uitsluitend taakstatusmetadata uit de bestaande broker. Loopt een andere
   gekoppelde taak nog, muteer de kaart niet: wacht via het bestaande taakmechanisme
   binnen de workerdeadline; bij blokkade rapporteer RCCAP, geen parallelle schrijver.
2. Gebruik `mindmap/public/current-projects.json`, de bestaande
   `docs/mindmaps/current-projects/writer.lock` (exclusieve flock), atomic write en
   `scripts/current-projects.py`. Bewaar vóór mutatie een taaksnapshot onder
   `docs/mindmaps/`; behoud histories, used_ids, bewijs en andere projecten.
   Koppel de eigen task_id/project_id onder de lock; een afgeronde root mag pending
   worden met een nieuwe eigen taaknode. Zet broker_status op `running` (Running).
   Publiceer precies één geel actief uitvoerbaar blad met titel
   `🔄 HUIDIGE STAP — ...` vóór de inhoudelijke uitvoering; controleer publicatie.
3. Houd tijdens uitvoering Running en precies één actief blad. Gebruik bestaande
   add/activate/complete/block-acties met `SERVER5_TASK_ID` gelijk aan de kaarttaak.
   Rond uitsluitend bewezen werk af met concreet bewijs. Snoei afgeronde subnodes
   direct; bewaar hun bewijs in de taaksnapshot. Behoud open blokkades en andere
   projecten. Groen betekent bewezen afgerond, nooit alleen een geslaagde commandexit.
4. Na succes: snoei de eigen voltooide tak volledig tot één groene samenvattende
   hoofdnode zonder kinderen. Als de hele kaart bewezen klaar is, reduceer haar tot
   één groene CURRENT-PROJECTS-samenvatting. Archiveer de volledige toestand eerst;
   behoud IDs/historie en zet broker_status `succeeded` (Succeeded). Bij fout of
   blokkade: `failed`/`blocked` (Failed/Blocked), behoud open nodes en publiceer RCCAP
   met oorzaak, oplossing en concrete volgende actie; claim geen succes.
5. Eindcontrole na ELKE taak, ook bij Failed/Blocked: gebruik de bestaande
   `web.mcp_mindmap.snapshot(ROOT)`-validator en lees de lokale gepubliceerde bron
   terug. Vereist: `consistent=true`, bronhash = publicatiehash,
   `project_invariants_valid=true`, geen afgeronde losse kinderen onder groene
   hoofdprojecten, exact nodeaantal vóór/tijdens/na vastgelegd. Controleer ook zelf
   dat iedere done-node een blad is (ook de root). Leg bewijs en rollback lokaal
   vast en rapporteer taakstatus, bestanden, nodeaantallen en volgende stap.
   Bij mislukte eindcontrole blijft de taak Failed/Blocked met RCCAP; nooit groen
   zonder bewijs. Brokerstatusmetadata niet vervalsen: de broker sluit zijn eigen
   taak af na workerexit; onderscheid kaartstatus van die nog lopende brokerstatus.

Deze bestaande AGENTS.md wordt voor iedere nieuwe worker gelezen via de centrale
RULES-instructie in web/commandcenter.py en de Codex-projectcontext (`-C` projectroot).
Dit is verplichte workeruitvoering, geen zelfstandige achtergrondautomatisering.
