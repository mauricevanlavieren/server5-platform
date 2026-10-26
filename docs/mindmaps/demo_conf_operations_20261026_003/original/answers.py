"""Deterministic demo answers, proposals only. No execution or external AI."""
import re,unicodedata
from data import dashboard,money

def answer(question):
 from workflow import view
 w=view()
 q=''.join(c for c in unicodedata.normalize('NFKD',question.lower()) if not unicodedata.combining(c));d=dashboard()
 if re.search(r'\b(verstuur|versturen|boek|betaal|bestel|voer uit|verzend)\b',q):
  result='Dit is alleen een demo-voorstel. Geen bericht, bestelling, betaling of boeking uitgevoerd. Bekijk het concept in het demoverhaal.'
 elif any(x in q for x in ['w105','cilinder','levering','planning','klussen','werkopdracht','morgen']):result='W105: '+w['status']+'. Afspraak '+w['appointment']+'. Levering '+w['delivery_at']+' ('+w['delivery_status']+'). '+w['todo']['Eigenaar']+' Cilinder SKG*** 30/35 mm. Contact: '+w['contact']
 elif re.search(r'\b(gisteren|morgen|vorige|volgende|week|maand|jaar)\b',q):result='De cijfers gelden alleen voor vaste demodag 26 oktober 2026. De genoemde levering op 27 oktober is onbevestigd.'
 elif any(n.lower() in q for n in d['staff']):
  names=[n for n in d['staff'] if n.lower() in q];rows=[o for o in d['orders'] if o['employee'] in names and o['status']!='afgerond']
  result='Openstaande klussen: '+('; '.join(f"{o['id']} {o['time']} {o['employee']}: {o['job']} — {o['status']}" for o in rows) or 'geen')+'. Afgeronde klussen zijn weggelaten.'
 elif 'omzet' in q:result=f"Omzet {money(d['revenue_cents'])} excl. btw uit definitieve facturen F101–F103. Betalingen apart: {money(d['payments_cents'])} incl. btw. Concept CF105 en open werk tellen niet mee."
 elif re.search(r'betaling|betaald|bank',q):result=f"Ontvangen {money(d['payments_cents'])}: B101 € 290,40 en B102 € 100,00. Dit is geen omzetcijfer."
 elif re.search(r'factuur|facturen|verlopen',q):result=f"Open {money(d['open_cents'])} incl. btw: F102 € 90,75 (30 oktober) en F103 € 117,80 (23 oktober, verlopen). CF105 is alleen concept."
 elif re.search(r'cilinder|voorraad|tekort|lever|probleem|onderdeel',q):result='W105 mist 1 veiligheidscilinder SKG*** 30/35 mm, nikkel, 3 sleutels. Demo Sluittechniek BV; verwacht 27 oktober 10:00, onbevestigd. Lina verifieert levering; Bram plaatst. Conceptklantbericht staat bij het tekort; niet verzonden.'
 elif re.search(r'planning|vandaag|klussen|werkopdracht',q):result='Open: W104 Bram 14:00 slot repareren; W105 Bram 16:00 cilinder, wacht op onderdeel; W106 Lina 15:00 offerte opvolgen.'
 elif re.search(r'opvolg|klant',q):result='Lina: W105 levering en conceptklantbericht beoordelen; W106 Kantoor Kade opvolgen. Niets verzonden.'
 elif re.search(r'ai|assistent|voorstel|gedaan|acties',q):result='Voorstellen: levering W105 laten verifiëren en restsaldo F103 beoordelen. Beide niet uitgevoerd. Tijdwinst is indicatief, niet bewezen.'
 else:result='Vraag naar omzet, betalingen, facturen, planning, cilindertekort, klantopvolging of wat Bram nog moet doen. Antwoorden zijn lokale regels, geen generatieve AI.'
 return dict(answer=result,source='Fictieve demo · 26 oktober 2026 · voorstel, geen uitvoering',provider='local-rules',external_calls=0,executed=False)
