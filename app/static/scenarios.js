document.querySelectorAll('[data-scenario]').forEach(button=>button.addEventListener('click',async()=>{
 const out=document.querySelector('#scenario-result');out.textContent='Launching scenario…';
 try{
  const response=await fetch('/api/demo/scenario/'+button.dataset.scenario,{method:'POST'});
  const run=await response.json();if(!response.ok)throw new Error(run.detail);
  out.textContent=run.label+' · '+run.request_id+' · '+run.company_ticket;
  const approve=document.createElement('button');approve.textContent='SIMULATE COMPANY STAFF APPROVAL';
  approve.onclick=async()=>{approve.disabled=true;try{
   await fetch('/api/company/approve/'+run.company_ticket,{method:'POST'});
   const v=await fetch('/api/verify/'+run.request_id,{method:'POST'});const result=await v.json();
   const line=document.createElement('p');line.textContent=result.status+' · leftovers '+result.leftover_count;out.append(line);
   if(result.status==='LEFTOVERS_FOUND')line.textContent+=' · use bounded retry action in request workflow';
  }catch(e){approve.disabled=false;line.textContent=e.message;}};
  out.append(approve);
 }catch(e){out.textContent=e.message;}
}));