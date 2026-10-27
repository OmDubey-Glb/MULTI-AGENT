async function scenarioPost(url){const response=await fetch(url,{method:'POST'});const data=await response.json();if(!response.ok)throw new Error(data.detail||'Action failed');return data;}
function addRetry(requestId,output,line){
 const retry=document.createElement('button');retry.textContent='SUBMIT BOUNDED RETRY';
 retry.onclick=async()=>{retry.disabled=true;try{
  const ticket=await scenarioPost('/api/retry/'+requestId);line.textContent='Retry '+ticket.retry_count+'/3 · '+ticket.company_ticket+' awaiting company approval';
  const approve=document.createElement('button');approve.textContent='APPROVE RETRY';
  approve.onclick=async()=>{approve.disabled=true;try{
   await scenarioPost('/api/company/approve/'+ticket.company_ticket);
   const result=await scenarioPost('/api/verify/'+requestId);
   line.textContent=result.status+' · leftovers '+result.leftover_count;
   if(result.status==='LEFTOVERS_FOUND')addRetry(requestId,output,line);
  }catch(error){line.textContent=error.message;approve.disabled=false;}};
  output.append(approve);
 }catch(error){line.textContent=error.message;retry.disabled=false;}};
 output.append(retry);
}
document.querySelectorAll('[data-scenario]').forEach(button=>button.addEventListener('click',async()=>{
 const out=document.querySelector('#scenario-result');out.textContent='Resetting and launching scenario…';
 try{
  await scenarioPost('/api/demo/reset');
  const run=await scenarioPost('/api/demo/scenario/'+button.dataset.scenario);
  out.textContent=run.label+' · '+run.request_id+' · '+run.company_ticket;
  const approve=document.createElement('button');approve.textContent='SIMULATE COMPANY STAFF APPROVAL';
  approve.onclick=async()=>{approve.disabled=true;try{
   await scenarioPost('/api/company/approve/'+run.company_ticket);
   const result=await scenarioPost('/api/verify/'+run.request_id);
   const line=document.createElement('p');line.textContent=result.status+' · leftovers '+result.leftover_count;out.append(line);
   if(result.status==='LEFTOVERS_FOUND')addRetry(run.request_id,out,line);
  }catch(error){approve.disabled=false;out.append(document.createTextNode(error.message));}};
  out.append(approve);
 }catch(error){out.textContent=error.message;}
}));