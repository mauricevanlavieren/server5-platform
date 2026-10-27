"""Fictional migration with preview, digest binding and atomic idempotent commit."""
import copy,csv,io,json,hashlib,re
from datetime import date,datetime,timezone

def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def preview_import(s,payload):
 if not isinstance(payload,dict) or set(payload)!={'batch_id','customers','articles','balances'}:raise ValueError('Verwacht batch_id, customers, articles en balances')
 if not isinstance(payload['batch_id'],str) or not re.fullmatch('[A-Za-z0-9_-]{1,60}',payload['batch_id']):raise ValueError('Ongeldig batch_id')
 errors=[];duplicates=[];seen={};customers=s.get('customers',{});articles=s.get('articles',{});existing=s.get('migration_sources',{})
 def error(kind,n,message):errors.append(dict(section=kind,line=n,message=message))
 def text(v,key):
  x=v.get(key)
  if not isinstance(x,str) or not x.strip() or len(x)>200:raise ValueError(key+': 1–200 tekens vereist')
  return x.strip()
 for kind,required in [('customers',{'id','name','address'}),('articles',{'id','name','unit_cents','vat_percent','quantity','location'}),('balances',{'id','customer_id','date','due','net_cents','vat_cents'})]:
  rows=payload[kind]
  if not isinstance(rows,list) or len(rows)>1000:raise ValueError(kind+': lijst van maximaal 1000 regels vereist')
  seen[kind]=set()
  for n,row in enumerate(rows,1):
   try:
    if not isinstance(row,dict) or set(row)!=required:raise ValueError('Velden vereist: '+', '.join(sorted(required)))
    ident=text(row,'id')
    if not re.fullmatch('[A-Za-z0-9_-]{1,60}',ident):raise ValueError('id: alleen letters, cijfers, _ en -')
    if ident in seen[kind]:raise ValueError('Dubbel bron-ID binnen bestand')
    seen[kind].add(ident)
    key=kind+':'+ident
    if key in existing:duplicates.append(dict(section=kind,line=n,message='Bron-ID al verwerkt: '+ident))
    if kind in {'customers','articles'}:
     name=text(row,'name');table=customers if kind=='customers' else articles
     if any(c.get('name','').casefold()==name.casefold() for c in table.values()) or any(r is not row and isinstance(r,dict) and r.get('name','').casefold()==name.casefold() for r in rows):duplicates.append(dict(section=kind,line=n,message='Mogelijk dubbel: naam '+name))
    if kind=='customers':text(row,'address')
    if kind=='articles':
     text(row,'location')
     if '@' in row['name'] or '@' in row['location']:raise ValueError('Artikelnaam en locatie mogen geen @ bevatten')
     for key in ['unit_cents','quantity']:
      if type(row[key]) is not int or not 0<=row[key]<=100000000:raise ValueError(key+': geheel niet-negatief getal vereist')
     if row['vat_percent']!=21:raise ValueError('Deze demo ondersteunt alleen 21% btw; andere tarieven vereisen uitbreiding')
     stockkey=row['name']+' @ '+row['location']
     if stockkey in s.get('operations',{}).get('stock',{}):duplicates.append(dict(section=kind,line=n,message='Bestaande voorraadlocatie: '+stockkey))
    if kind=='balances':
     text(row,'customer_id')
     # Exact customer ID references, never fuzzy matching.
     candidate_ids={r.get('id') for r in payload['customers'] if isinstance(r,dict)} if isinstance(payload['customers'],list) else set()
     if row['customer_id'] not in customers and row['customer_id'] not in candidate_ids:raise ValueError('Onbekend klant-ID')
     for key in ['date','due']:
      value=text(row,key)
      if date.fromisoformat(value).isoformat()!=value:raise ValueError('ISO bedrijfsdatum vereist')
     if row['due']<row['date']:raise ValueError('Vervaldatum ligt vóór documentdatum')
     if type(row['net_cents']) is not int or type(row['vat_cents']) is not int or row['net_cents']<=0 or row['vat_cents']<0 or row['net_cents']+row['vat_cents']>100000000:raise ValueError('Saldo: positieve netto centen en niet-negatieve btw vereist')
     if row['vat_cents']!=(row['net_cents']*21+50)//100:raise ValueError('Btw moet overeenkomen met 21% van het resterende nettosaldo')
     from data import INVOICES
     ids={i['id'] for i in INVOICES}|{i.get('id') for j in s.get('jobs',{}).values() for i in [j.get('sales_invoice',{})]+j.get('invoice_archive',[])}
     if ident in ids:duplicates.append(dict(section=kind,line=n,message='Factuurnummer bestaat al'))
   except (ValueError,TypeError) as e:error(kind,n,str(e))
 fingerprint=digest(payload);old=next((h for h in s.get('migration_history',[]) if h['batch_id']==payload['batch_id']),None)
 repeated=bool(old and old['digest']==fingerprint)
 if old and not repeated:errors.append(dict(section='batch',line=0,message='Batch-ID al met andere inhoud verwerkt'))
 totals=dict(customers=len(payload['customers']),articles=len(payload['articles']),stock_quantity=sum(r.get('quantity',0) for r in payload['articles'] if isinstance(r,dict) and type(r.get('quantity')) is int),balances=len(payload['balances']),opening_cents=sum(r.get('net_cents',0)+r.get('vat_cents',0) for r in payload['balances'] if isinstance(r,dict) and type(r.get('net_cents')) is int and type(r.get('vat_cents')) is int))
 return dict(digest=fingerprint,revision=s['revision'],errors=errors,duplicates=duplicates,totals=totals,already_processed=repeated,can_commit=not errors and (repeated or not duplicates),note='Alleen fictieve data. Beginsaldi zijn resterende vorderingen, geen nieuwe omzet of historische ontvangsten.')

def commit_import(s,v):
 payload=v.get('payload');preview=preview_import(s,payload)
 if preview['digest']!=v.get('preview_digest'):raise ValueError('Bestand gewijzigd na voorvertoning; controleer opnieuw')
 if not preview['can_commit']:raise ValueError('Los regelfouten en mogelijke duplicaten op vóór verwerken')
 if preview['already_processed']:return
 customers=s.setdefault('customers',{});articles=s.setdefault('articles',{});sources=s.setdefault('migration_sources',{});ops=s.setdefault('operations',{})
 for k in ('orders','stock','reservations','sales','purchases'):ops.setdefault(k,{})
 for c in payload['customers']:customers[c['id']]=copy.deepcopy(c);sources['customers:'+c['id']]=payload['batch_id']
 for a in payload['articles']:
  articles[a['id']]=copy.deepcopy(a);ops['stock'][a['name']+' @ '+a['location']]=a['quantity'];sources['articles:'+a['id']]=payload['batch_id']
 for b in payload['balances']:
  ident='WIM_'+b['id'];customer=customers[b['customer_id']]['name'];total=b['net_cents']+b['vat_cents']
  ops['orders'][ident]=dict(id=ident,customer=customer,scope='Geïmporteerd restant '+b['id'],status='beginsaldo',kind='import',source=payload['batch_id'])
  inv=dict(id=b['id'],status='verstuurd (gesimuleerd)',issued_date=b['date'],due=b['due'],net_cents=b['net_cents'],vat_cents=b['vat_cents'],total_cents=total,paid_cents=0,payments=[],credits=[],refunds=[],opening_balance=True,legacy=True,lines=[dict(description='Resterende vordering bij proefmigratie',quantity=1,unit_cents=b['net_cents'],net_cents=b['net_cents'],vat_percent=21,source='Fictieve bron '+payload['batch_id'])])
  s.setdefault('jobs',{})[ident]=dict(completed=True,status='beginsaldo',sales_invoice=inv,legacy=True)
  sources['balances:'+b['id']]=payload['batch_id']
 s.setdefault('migration_history',[]).append(dict(batch_id=payload['batch_id'],digest=preview['digest'],totals=preview['totals'],actor=v.get('actor'),at=datetime.now(timezone.utc).isoformat(),business_date=__import__('data').DAY))

def reconcile():
 from data import dashboard,accounting_csv
 from workflow import view
 d=dashboard();s=view();rows=list(csv.DictReader(io.StringIO(accounting_csv().decode('utf-8-sig')),delimiter=';'))
 def amount(r,key):return int(r[key] or 0)
 cash_types={'payment','payment_reversal','refund','sale_payment','sale_refund'}
 revenue_types={'invoice','sale','credit','sale_return'}
 opening_ids={r['original_invoice'] for r in rows if r['record_type']=='opening_balance'}
 export=dict(revenue_cents=sum(amount(r,'net_cents') for r in rows if r['record_type'] in revenue_types and r['original_invoice'] not in opening_ids),net_received_cents=sum(amount(r,'cashflow_effect_cents') for r in rows),open_cents=sum(amount(r,'open_cents') for r in rows if r['record_type'] in {'invoice','sale','opening_balance'}))
 expected=dict(revenue_cents=d['revenue_cents'],net_received_cents=d['payments_cents'],open_cents=d['open_cents'])
 differences=[dict(field=k,expected=expected[k],export=export[k],difference=export[k]-expected[k]) for k in expected if export[k]!=expected[k]]
 issues=[];parents={r['id'] for r in rows if r['record_type'] in {'invoice','sale','opening_balance'}};pays={r['id'] for r in rows if r['record_type']=='payment'};keys=set()
 for n,r in enumerate(rows,2):
  k=(r['record_type'],r['id'])
  if k in keys:issues.append(dict(line=n,message='Dubbel document/event-ID'))
  keys.add(k)
  if r['original_invoice'] not in parents:issues.append(dict(line=n,message='Ontbrekend oorspronkelijk document'))
  if r['parent_payment'] and r['parent_payment'] not in pays:issues.append(dict(line=n,message='Ontbrekende betaalreferentie'))
  if r['date']=='UNKNOWN' or r['missing_fields']:issues.append(dict(line=n,id=r['id'],message='Bronvelden ontbreken: '+(r['missing_fields'] or 'date')))
  if r['date']!='UNKNOWN':
   try:date.fromisoformat(r['date'])
   except ValueError:issues.append(dict(line=n,message='Ongeldige bedrijfsdatum'))
  if r['record_type'] in {'invoice','sale','opening_balance','credit','sale_return'} and amount(r,'net_cents')+amount(r,'vat_cents')!=amount(r,'total_cents'):differences.append(dict(field=r['id'],difference=amount(r,'net_cents')+amount(r,'vat_cents')-amount(r,'total_cents')))
 for i in d['invoices']:
  cash=sum(amount(r,'cashflow_effect_cents') for r in rows if r['original_invoice']==i['id'])
  if i['total_cents']-i.get('credits_cents',0)-cash!=i['open_cents']:differences.append(dict(field=i['id'],message='Document, credit en geld sluiten niet aan'))
 return dict(balanced=not differences,ready_for_external_import=not differences and not issues,expected=expected,export=export,differences=differences,source_issues=issues,export_rows=len(rows),opening_balances_cents=sum(amount(r,'total_cents') for r in rows if r['record_type']=='opening_balance'),external_import='niet gevalideerd',business_date=d['day'],generated_at=datetime.now(timezone.utc).isoformat(),revision=s['revision'])
