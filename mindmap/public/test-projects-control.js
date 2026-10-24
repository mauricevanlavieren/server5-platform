'use strict';
(() => {
 const form=document.querySelector('#execute-form'), result=document.querySelector('#execute-result');
 const input=document.querySelector('#execute-prompt'), button=document.querySelector('#execute');
 const broker='https://server5.taile88688.ts.net';
 if(location.port==='8788') {
   const link=document.querySelector('#broker-open');link.hidden=false;link.href=broker+'/test-projects.html';
   input.disabled=true;button.disabled=true;result.textContent='Open de beveiligde Commandcenter om expliciet uit te voeren.';return;
 }
 let pending;
 try { pending=JSON.parse(sessionStorage.getItem('test-project-submit')||'null'); } catch {}
 if(pending) input.value=pending.prompt;
 form.onsubmit=async e=>{
   e.preventDefault();if(!document.querySelector('#owner-click').checked)return;
   button.disabled=true;
   try {
     const session=await fetch('/api/session',{cache:'no-store'});
     if(!session.ok){result.textContent='Meld je eerst aan via Commandcenter en keer terug naar TEST PROJECTS.';const a=document.createElement('a');a.href='/';a.textContent='Aanmelden';result.append(a);return;}
     const {csrf}=await session.json();
     if(pending && pending.prompt!==input.value)throw Error('Onzeker eerder verzoek: herstel eerst de oorspronkelijke tekst of controleer de queue.');
     pending=pending||{key:crypto.randomUUID().replaceAll('-',''),prompt:input.value,owner_click:true};
     sessionStorage.setItem('test-project-submit',JSON.stringify(pending));
     const response=await fetch('/api/test-projects/execute',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:JSON.stringify(pending)});
     const task=await response.json();if(!response.ok)throw Error(task.error||`HTTP ${response.status}`);
     result.textContent=`Taak ${task.id}: ${task.status}. Live voortgang verschijnt in deze kaart.`;
     sessionStorage.removeItem('test-project-submit');pending=null;input.value='';document.querySelector('#owner-click').checked=false;
   } catch(err){result.textContent=err.message;} finally {button.disabled=false;}
 };
})();
