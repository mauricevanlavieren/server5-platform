"""Pure package-neutral accounting serializer. No database, network or domain imports.

A future chosen target adapter consumes schema_version=1 snapshots; it must not
change invoices, credits, cash events or business rules. No target is selected.
"""
import csv,io,json,hashlib

def export_csv(snapshot):
 if snapshot.get('schema_version')!=1 or snapshot.get('currency')!='EUR':raise ValueError('Unsupported accounting snapshot schema/currency')
 out=io.StringIO();writer=csv.writer(out,delimiter=';')
 header=['record_type','id','original_invoice','parent_payment','order','date','due','net_cents','vat_cents','total_cents','received_cents','credit_cents','refund_cents','open_cents','currency','customer','method','reference_or_reason','accounting_state','source_sha256','metadata_status','missing_fields','required_mappings','net_received_cents','cashflow_effect_cents','recorded_at']
 writer.writerow(header)
 for document in snapshot['documents']:
  inv=document['invoice'];job=document['order'];b=document['balance'];digest=document['source_sha256'];state=document['accounting_state']
  def row(kind,ident,day,net='',vat='',total='',method='',ref='',parent='',source_status='',missing='',recorded_at=None):
   writer.writerow([kind,ident,inv['id'],parent,job,day or 'UNKNOWN',inv.get('due','UNKNOWN'),net,vat,total,b['received_cents'],b['credits_cents'],b['refunded_cents'],b['open_cents'],'EUR',document['customer'],method or 'UNKNOWN',ref or 'UNKNOWN',state,digest,source_status,missing,'debiteur_id|dagboek|grootboek|btw_code; centen naar decimalen; bron controleren',b['received_cents']-b['refunded_cents'],total if kind in {'payment','payment_reversal','refund'} else 0,recorded_at or 'UNKNOWN'])
  row('opening_balance' if inv.get('opening_balance') else 'invoice',inv['id'],inv.get('issued_date'),inv['net_cents'],inv['vat_cents'],inv['total_cents'],ref=inv.get('replaces'),missing='issued_date' if not inv.get('issued_date') else '',recorded_at=inv.get('recorded_at'))
  for index,edit in enumerate(inv.get('date_history',[])):row('invoice_date_metadata',inv['id']+'-D'+str(index+1),edit['after'],ref=edit['source']+' · oorspronkelijk: '+str(edit['before']))
  for cr in inv.get('credits',[]):row('credit',cr['id'],cr['date'],-cr['net_cents'],-cr['vat_cents'],-cr['total_cents'],ref=cr['reason'],recorded_at=cr.get('at'))
  for n,pay in enumerate(inv.get('payments',[])):
   pid=pay['id'];missing='|'.join(k for k in ['date','method','reference'] if not pay.get(k));status=pay.get('source_status') or ('unverified' if missing else 'recorded')
   row('payment',pid,pay.get('date'),total=pay['cents'],method=pay.get('method'),ref=pay.get('reference'),source_status=status,missing=missing,recorded_at=pay.get('at'))
   if pay.get('reversal'):row('payment_reversal',pid+'-REV',pay['reversal']['date'],total=-pay['cents'],parent=pid,ref=pay['reversal']['reason'],recorded_at=pay['reversal'].get('at'))
   for index,edit in enumerate(pay.get('metadata_history',[])):row('payment_metadata',pid+'-M'+str(index+1),edit['at'][:10],parent=pid,ref=edit['reason']+' · '+json.dumps(dict(before=edit['before'],after=edit['after']),ensure_ascii=False),source_status=edit['after']['source_status'])
  for pay in inv.get('refunds',[]):row('refund',pay['id'],pay['date'],total=-pay['cents'],method=pay['method'],ref=pay['reference'],recorded_at=pay.get('at'))
 for sale in snapshot['sales']:
  digest=hashlib.sha256(json.dumps(sale,sort_keys=True).encode()).hexdigest()
  def sale_row(kind,ident,net='',vat='',total='',ref='',day=None,recorded_at=None):
   writer.writerow([kind,ident,sale['id'],'','winkelbalie',day or 'UNKNOWN','',net,vat,total,sale['paid_cents'],sum(r['total_cents'] for r in sale.get('returns',[])),sum(r['total_cents'] for r in sale.get('returns',[])),0,'EUR','Winkelbalie','cash',ref,'pending',digest,'recorded' if day else 'unverified','date' if not day else '','kasdagboek|grootboek|btw_code',sale['paid_cents']-sum(r['total_cents'] for r in sale.get('returns',[])),total if kind in {'sale_payment','sale_refund'} else 0,recorded_at or sale.get('recorded_at') or 'UNKNOWN'])
  sale_row('sale',sale['id'],sale['net_cents'],sale['vat_cents'],sale['total_cents'],ref=sale['source'],day=sale.get('date'))
  sale_row('sale_payment','P'+sale['id'],total=sale['paid_cents'],ref='Fictieve contante verkoop '+sale['id'],day=sale.get('date'))
  for r in sale.get('returns',[]):
   sale_row('sale_return',r['id'],-r['net_cents'],-r['vat_cents'],-r['total_cents'],r['reason'],r['date'],recorded_at=r.get('at'))
   sale_row('sale_refund',r['id']+'-T',total=-r['total_cents'],ref=r['reason'],day=r['date'],recorded_at=r.get('at'))
 return ('\ufeff'+out.getvalue()).encode('utf-8')
