'use strict';
let csrf='',selected=null,cursor=0,logText='',busy=false;
const $=id=>document.getElementById(id);
const labels={queued:'In wachtrij',running:'Bezig',succeeded:'Geslaagd',failed:'Mislukt',cancelled:'Gestopt',interrupted:'Onderbroken na herstart'};
async function api(path,options={}){
  const response=await fetch(path,{cache:'no-store',...options,headers:{'Content-Type':'application/json',...(csrf?{'X-CSRF-Token':csrf}:{}),...(options.headers||{})}});
  const data=await response.json();
  if(!response.ok){if(response.status===401){csrf='';show(false);}throw new Error(data.error||'Verzoek mislukt');}
  return data;
}
function show(on){$('login').hidden=on;$('workspace').hidden=!on;}
function error(err){$('error').textContent=err?String(err.message||err):'';}
async function copyTaskId(id){
  const status=$('copy-status');
  status.textContent='';
  try{
    await navigator.clipboard.writeText(id);
    status.textContent='Taak-ID gekopieerd.';
    return;
  }catch{}
  const field=document.createElement('textarea');
  const previous=document.activeElement;
  field.value=id;field.readOnly=true;field.className='clipboard-copy';
  field.setAttribute('aria-hidden','true');field.tabIndex=-1;
  try{
    document.body.append(field);field.focus();field.select();field.setSelectionRange(0,id.length);
    if(!document.execCommand('copy'))throw new Error('Kopiëren niet beschikbaar');
    status.textContent='Taak-ID gekopieerd.';
  }catch{
    status.textContent='Kopiëren niet gelukt. Selecteer het taak-ID en kopieer het handmatig.';
  }finally{
    field.remove();if(previous?.isConnected)previous.focus({preventScroll:true});
  }
}
async function select(id){selected=id;cursor=0;logText='';$('log').textContent='Laden…';await refresh();if(innerWidth<760)$('detail-title').scrollIntoView({behavior:'smooth',block:'start'});}
async function refresh(){
  if(!csrf||busy)return;busy=true;
  try{
    const tasks=await api('/api/tasks');
    $('tasks').replaceChildren();$('count').textContent=tasks.length+' bewaard';
    if(!tasks.length){const p=document.createElement('p');p.className='muted';p.textContent='Nog geen opdrachten.';$('tasks').append(p);}
    for(const task of tasks){
      const row=document.createElement('article');row.className='task'+(task.id===selected?' selected':'');
      const open=document.createElement('button');open.type='button';open.className='task-open';
      const title=document.createElement('strong');title.textContent=task.prompt;
      const meta=document.createElement('span');meta.textContent=(labels[task.status]||task.status)+' · '+new Date(task.created*1000).toLocaleString('nl-NL');
      open.append(title,meta);open.onclick=()=>select(task.id).catch(error);
      const identity=document.createElement('div');identity.className='task-identity';
      const id=document.createElement('code');id.textContent=task.id;id.setAttribute('aria-label','Taak-ID '+task.id);
      const copy=document.createElement('button');copy.type='button';copy.className='secondary';copy.textContent='Kopieer ID';
      copy.setAttribute('aria-label','Kopieer taak-ID '+task.id);copy.onclick=()=>copyTaskId(task.id);
      identity.append(id,copy);row.append(open,identity);$('tasks').append(row);
    }
    if(selected){const task=await api('/api/tasks/'+selected);$('task-prompt').textContent=task.prompt;$('task-meta').textContent=(labels[task.status]||task.status)+(task.cancel?' · stop aangevraagd':'')+(task.exit_code!==null?' · exit '+task.exit_code:'');$('cancel').hidden=!(['queued','running'].includes(task.status)||['queued','running'].includes(task.goal?.status));$('result').textContent=(task.goal?('Project '+task.goal.id+' · '+task.goal.status+' · etappe '+task.goal.stages+'/'+task.goal.max_stages+'\n'+task.goal.reason+'\nCheckpoint: '+task.goal.checkpoint+'\n\n'):'')+(task.result||(['queued','running'].includes(task.status)?'Codex werkt aan deze opdracht. Bekijk het uitvoeringslog voor de laatste gebeurtenissen.':'Geen resultaattekst; bekijk de log.'));const events=await api('/api/tasks/'+selected+'/events?after='+cursor);for(const event of events){cursor=event.seq;logText+=new Date(event.at*1000).toLocaleTimeString('nl-NL')+' '+event.text+'\n';}logText=logText.slice(-160000);$('log').textContent=logText||'Nog geen uitvoeringsmeldingen.';}
    $('connection').textContent='Verbonden met server5';
  }catch(err){$('connection').textContent='Verbinding controleren';error(err);}finally{busy=false;}
}
$('login-form').onsubmit=async event=>{event.preventDefault();error();try{const data=await api('/api/login',{method:'POST',body:JSON.stringify({password:$('password').value})});$('password').value='';csrf=data.csrf;show(true);await refresh();}catch(err){error(err);}};
$('task-form').onsubmit=async event=>{event.preventDefault();error();$('submit').disabled=true;try{const task=await api('/api/tasks',{method:'POST',body:JSON.stringify({prompt:$('prompt').value,key:crypto.randomUUID().replaceAll('-',''),parent:$('follow').checked?selected:null,goal:$('project').checked?{criteria:$('criteria').value,max_stages:4,max_seconds:3600}:null})});$('prompt').value='';$('confirm').checked=false;await select(task.id);}catch(err){error(err);}finally{$('submit').disabled=false;}};
$('cancel').onclick=async()=>{if(!selected||!confirm('Stop deze opdracht? Eerdere wijzigingen blijven bestaan.'))return;try{await api('/api/tasks/'+selected+'/cancel',{method:'POST',body:'{}'});await refresh();}catch(err){error(err);}};
$('logout').onclick=async()=>{try{await api('/api/logout',{method:'POST',body:'{}'});csrf='';selected=null;logText='';$('log').textContent='—';$('result').textContent='—';show(false);}catch(err){error(err);}};
(async()=>{try{const data=await api('/api/session');csrf=data.csrf;$('mcp-cancel-proof').hidden=!data.mcp_cancel_confirmation;show(true);await refresh();}catch(err){show(false);$('connection').textContent='Aanmelden';}})();
setInterval(refresh,2000);

$('mcp-cancel-proof').onclick=async()=>{
  if(!selected)return;
  const taskId=selected, requestId=prompt('Vul de exacte request_id van de MCP-stop in (16–80 letters/cijfers/_/-).');
  if(!requestId||!/^[A-Za-z0-9_-]{16,80}$/.test(requestId))return;
  if(!confirm('Bevestig MCP-stop voor taak '+taskId+' met request_id '+requestId+'. Eerdere wijzigingen blijven bestaan. Dit bewijs is 60 seconden geldig; deel het alleen met je vertrouwde client.'))return;
  try{
    const proof=await api('/api/tasks/'+taskId+'/mcp-cancel-confirmation',{method:'POST',body:JSON.stringify({request_id:requestId,confirmed:true})});
    const receipt=$('mcp-cancel-receipt');receipt.textContent=JSON.stringify(proof,null,2);receipt.hidden=false;
    setTimeout(()=>{receipt.textContent='';receipt.hidden=true;},60000);
  }catch(err){error(err);}
};
