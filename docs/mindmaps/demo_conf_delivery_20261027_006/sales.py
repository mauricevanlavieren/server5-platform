"""Append-only fictional tour preparation; never reset other dossiers or histories."""
from datetime import datetime,timezone

def prepare(s,v):
 from business import operate
 ops=s.setdefault('operations',{});runs=ops.setdefault('demo_runs',[]);ident='D'+str(len(runs)+1)
 customer='Rondleiding '+ident+' — fictief';article='Rondleiding '+ident+' cilinder'
 def op(action,**kw):operate(s,dict(action=action,role='Eigenaar',job='W104',**kw))
 op('quote_new',priority='normaal',customer=customer+' monteur',contact='Fictieve klant',scope='Cilinder monteren met herleidbare offerte')
 a=list(ops['orders'])[-1]
 op('intake',customer=customer+' onderdeel',contact='Fictieve klant',scope='Diagnose en vervolg bij ontbrekend onderdeel',priority='normaal',address='Fictieve Voorbeeldstraat',phone='000',access='Fictief contact; geen codes')
 b=list(ops['orders'])[-1]
 op('stock_receive',part=article,location='winkel',quantity=4,source='Fictieve startvoorraad uitsluitend voor oefenronde '+ident)
 runs.append(dict(id=ident,created_at=datetime.now(timezone.utc).isoformat(),monteur=a,onderdeel=b,article=article,quantity=4,source='Bewust door eigenaar gemaakte oefenronde; eerdere rondes/historie behouden'))
