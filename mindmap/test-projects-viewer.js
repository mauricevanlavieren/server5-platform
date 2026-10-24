import { startCodexStatus } from './codex-status.mjs';
import { Markmap } from 'markmap-view';
const escape = text => String(text).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let map, previous;
const project = n => ({content:`<strong class="${n.status}">${escape(n.title)}${n.status==='active'?' · ACTIEF':''}${n.status==='done'?' · VOLTOOID':''}${n.block?` · GEBLOKKEERD<br>Oorzaak: ${escape(n.block.cause)}<br>Oplossing: ${escape(n.block.solution)}<br>Volgende actie: ${escape(n.block.next_action)}`:''}</strong>`,payload:{liveId:n.id},children:n.children.map(project)});
async function refresh(){
 try {
  const r=await fetch('./test-projects.json',{cache:'no-store'});
  if(!r.ok) throw Error(`HTTP ${r.status}`);
  const s=await r.json();
  if(JSON.stringify(s)!==previous){
   previous=JSON.stringify(s);
   if(!map) map=Markmap.create('#mindmap',{maxWidth:400,duration:0},project(s.root));
   else await map.setData(project(s.root));
   await map.fit();
  }
  document.querySelector('#status').textContent=`${s.label} · laatste echte update ${s.updated_at}`;
 } catch(e){document.querySelector('#status').textContent=`Laden mislukt: ${e.message}`;}
}
document.querySelector('#fit').onclick=()=>map?.fit();
refresh();setInterval(refresh,3000); // Reads only; never advances task state.

import './public/test-projects-control.js';

startCodexStatus();
