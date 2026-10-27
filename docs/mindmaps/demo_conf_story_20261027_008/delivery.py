"""Trial proposal, explicit owner decisions and attributable staff self-assessments."""
from datetime import datetime,timezone
import copy,json,csv,io,collections
FIELDS={'trial_start':'Startdatum proef','trial_end':'Einddatum proef','pilot_lead':'Begeleider / aanspreekpunt','one_time_cost':'Eenmalige inrichting incl./excl. btw','recurring_cost':'Periodieke prijs en inbegrepen gebruik','included':'Inbegrepen functies en koppelingen','excluded':'Uitgesloten werkzaamheden','migration_training':'Migratie en training','support_contact':'Ondersteuningscontact','support_details':'Contactgegevens ondersteuning','support_hours':'Bereikbaarheid ondersteuning','incident_response':'Storingsafhandeling en reactieafspraak','hosting':'Hosting en verantwoordelijkheden','backup_destination':'Door eigenaar te kiezen bestemming buiten Server4','backup_policy':'Back-upfrequentie, retentie en verantwoordelijke','recovery_goal':'Hersteldoelen en testafspraak','contract_term':'Looptijd','cancellation':'Opzegging','data_exit':'Gegevensuitvoer bij vertrek','accounting_package':'Boekhoudpakket','accounting_environment':'Geautoriseerde boekhoudtestomgeving','mapping_notes':'Debiteur-, dagboek-, grootboek- en btw-mapping'}
CASES={
'mechanic':dict(title='Monteur: eigen opdracht uitvoeren',steps=[('assignment','Eigen toegewezen opdracht en afspraak vinden'),('execution','Bevindingen, werkelijke uren en materiaal zelfstandig opslaan'),('material','Materiaalverbruik en open reserveringen controleren'),('handoff','Gereedmelden en overdracht aan administratie controleren'),('reload','Herladen: eigen registratie behouden')]),
'shop':dict(title='Winkel: verkoop en gedeeltelijke retour',steps=[('stock','Vrije voorraad en artikel controleren'),('sale','Fictieve verkoop opslaan; voorraad en bedrag controleren'),('return','Gedeeltelijke retour met reden en datum verwerken'),('cash','Fictieve terugbetaling en resterende voorraad controleren'),('reload','Herladen: verkoop en retourhistorie behouden')]),
'administration':dict(title='Administratie: factuur tot afsluiting',steps=[('handoff','Gereedgemeld dossier en overgenomen uren/materiaal vinden'),('invoice','Eigenaarstarieven controleren; concept en btw beoordelen'),('payment','Definitieve factuur, fictieve betaling en debiteur controleren'),('reconcile','Netto omzet, debiteuren en geld met export afstemmen'),('accounting','Resterend boekhoudhandwerk en ontbrekende bronvelden noteren')])}

def read(s,status_path=None):
 trial=copy.deepcopy(s.get('trial',{}));evidence={}
 if status_path and status_path.exists():
  try:evidence=json.loads(status_path.read_text())
  except (OSError,ValueError):evidence={}
 if not trial.get('decisions',{}).get('backup_destination') or not evidence.get('owner_confirmed'):
  evidence=dict(result='PENDING_OWNER_DECISION',message='Externe back-up: nog niet ingericht en getest',owner_decision_required=True)
 if evidence.get('result')=='PASS':
  try:evidence['age_hours']=round((datetime.now(timezone.utc)-datetime.fromisoformat(evidence['completed_at'])).total_seconds()/3600,1);evidence['stale']=evidence['age_hours']>26
  except (ValueError,KeyError):evidence['stale']=True
 records=trial.get('acceptance',[])
 # A demo walkthrough never counts as independent staff acceptance.
 accepted={k:any(a['case_id']==k and a['outcome']=='passed' and a.get('actor',{}).get('role')==k for a in records) for k in CASES}
 return dict(revision=s['revision'],fields=FIELDS,decisions=trial.get('decisions',{}),decision_history=trial.get('decision_history',[]),cases=CASES,acceptance=records,staff_self_reported=accepted,external_backup=evidence,external_import='niet gevalideerd',proposal_status='Concept voor begeleide fictieve praktijkproef; geen overeengekomen aanbod of ondersteuning',scope=['Drie bestaande bedrijfsroutes, met uitsluitend fictieve gegevens','Bestaande persoonlijke accounts voor monteur, winkel en administratie','Controle van voorraad, btw, credits, geld en herleidbaarheid','Eén proefmigratie en gezamenlijke boekhoudvoorbereiding','Back-up op andere host met geïsoleerde herstelcontrole'],gates=['Start alleen met gekozen begeleider, deelnemers, periode en expliciete kostenafspraak','Geen echte gegevens of transacties vóór afzonderlijke toestemming en beheer-/privacyafspraken','Boekhoudimport pas bewezen na geautoriseerde testimport en teruggelezen bewijs','Gezamenlijke evaluatie na de drie routes; handwerk, fouten en herstel vastleggen','Besluit apart over vervolgproef, aanschaf en productie'])

def authorize(u,v):
 if v.get('action')=='trial_decisions':
  if u['role']!='owner':raise ValueError('Alleen eigenaar kan zakelijke keuzes vastleggen')
 elif v.get('action')=='trial_accept':
  case=v.get('case_id')
  if case not in CASES or (u['role'] not in {'owner','demo'} and u['role']!=case):raise ValueError('Registreer uitsluitend je eigen medewerkersroute')
 else:raise ValueError('Onbekende proefactie')
 return dict(v,role='Eigenaar',actor=dict(u))

def mutate(s,v):
 trial=s.setdefault('trial',{});now=datetime.now(timezone.utc).isoformat();actor=v.get('actor') or {}
 if v['action']=='trial_decisions':
  values=v.get('values');reference=v.get('reference','')
  if not isinstance(values,dict) or set(values)-set(FIELDS) or not isinstance(reference,str) or not reference.strip() or len(reference)>500:raise ValueError('Bekende velden en bron/akkoordreferentie vereist')
  if any(not isinstance(x,str) or len(x)>1500 for x in values.values()):raise ValueError('Keuzeveld: maximaal 1500 tekens')
  for key in ('trial_start','trial_end'):
   if values.get(key):
    from datetime import date
    if date.fromisoformat(values[key]).isoformat()!=values[key]:raise ValueError('Gebruik ISO datum')
  start=values.get('trial_start',trial.get('decisions',{}).get('trial_start',{}).get('value',''));end=values.get('trial_end',trial.get('decisions',{}).get('trial_end',{}).get('value',''))
  if start and end and end<start:raise ValueError('Einddatum ligt vóór startdatum')
  before=copy.deepcopy(trial.get('decisions',{}));new=trial.setdefault('decisions',{})
  for k,value in values.items():
   if not value.strip():continue # Unknown stays unknown; do not clear established decisions silently.
   new[k]=dict(value=value.strip(),actor=actor,at=now,reference=reference.strip(),status='door eigenaar vastgelegd; externe afspraken niet onafhankelijk geverifieerd')
  trial.setdefault('decision_history',[]).append(dict(before=before,after=copy.deepcopy(new),actor=actor,at=now,reference=reference.strip()))
 else:
  case=v['case_id'];outcome=v.get('outcome');steps=v.get('steps');note=v.get('note')
  if outcome not in {'passed','failed','blocked'} or not isinstance(note,str) or not note.strip() or len(note)>2000:raise ValueError('Resultaat en concrete bevinding/bewijsreferentie vereist')
  required={k for k,_ in CASES[case]['steps']}
  if not isinstance(steps,list) or any(not isinstance(x,str) for x in steps) or len(set(steps))!=len(steps) or not set(steps)<=required:raise ValueError('Ongeldige controlestappen')
  if outcome=='passed' and set(steps)!=required:raise ValueError('Beoordeel alle stappen vóór geslaagd')
  trial.setdefault('acceptance',[]).append(dict(id='P'+str(len(trial.get('acceptance',[]))+1),case_id=case,outcome=outcome,steps=steps,note=note.strip(),actor=actor,at=now,evidence_type='eigen waarneming deelnemer; geen onafhankelijke technische certificering'))

def accounting_preparation():
 from pilot import reconcile
 from data import accounting_csv
 report=reconcile();rows=list(csv.DictReader(io.StringIO(accounting_csv().decode('utf-8-sig')),delimiter=';'))
 missing=collections.Counter()
 for r in rows:
  if r['date']=='UNKNOWN':missing['bedrijfsdatum']+=1
  for k in filter(None,r['missing_fields'].split('|')):
   if k not in {'date','issued_date'}:missing[{'reference':'betaalreferentie','method':'betaalmethode'}.get(k,k)]+=1
 document_ids={r['original_invoice'] for r in rows};types=collections.Counter(r['record_type'] for r in rows)
 return dict(revision=report['revision'],balanced=report['balanced'],totals=report['expected'],source_issues=report['source_issues'],missing_field_counts=dict(missing),records=len(rows),documents=len(document_ids),record_types=dict(types),external_import='niet gevalideerd',remaining_manual_work=['Historische bronproblemen aanvullen met echte bewijsstukken; onbekend niet als nul invullen','Stabiele debiteuren koppelen aan testadministratie','Dagboeken, grootboekrekeningen en btw-codes per documentsoort vastleggen','Importformaat/tekens en EUR-centen naar doelpakket vertalen','Facturen, credits, betalingen en retouren in doelpakket importeren en koppelen','Doelpakket teruglezen: aantallen, nettobedragen, btw, open posten en ontvangen geld vergelijken'],validation_protocol=['Kies pakket, geautoriseerde testadministratie en uitvoerder','Bewaar beginsnapshot van de testadministratie en bronexport','Leg verwachte aantallen, omzet na credits, btw, debiteuren en geld vooraf vast','Importeer één gecontroleerde fictieve batch; geen echte productieboeking','Lees doelpakket terug en vergelijk alle bedragen en relaties, ook credits en betalingen','Herhaal alleen volgens deduplicatie-afspraak en bewijs dat niets dubbel staat','Bewaar doelrapport/import-ID en afwijkingen; eigen verklaring is geen onafhankelijke validatie'],time_saved='Niet gemeten; noteer tijdens de echte proef hoeveel velden en minuten handwerk overblijven')
