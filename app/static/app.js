const $ = (s) => document.querySelector(s);
let sessionId = null;
let verified = false;
let selected = [];
let categoryCatalog = [];
async function api(path, options={}) {
  const response = await fetch(path, {headers:{'Content-Type':'application/json'}, ...options});
  const data = await response.json().catch(()=>({detail:'Unexpected server response'}));
  if(!response.ok) throw new Error(data.detail || 'Request failed');
  return data;
}
function message(text, kind='') { $('#intake-message').textContent=text; $('#intake-message').className='form-message '+kind; }
async function refreshAgents(){try{const d=await api('/api/agents');$('#agent-list').innerHTML=d.agents.map(a=>'<div class="agent"><span>'+a.name+'</span><b>'+a.status+'</b></div>').join('');}catch{}}
function logEvent(e){const empty=$('.empty');if(empty)empty.remove();const row=document.createElement('div');row.className='log';const time=new Date(e.timestamp||Date.now()).toLocaleTimeString();const status=e.status||'INFO';const tag=document.createElement('span');tag.className='tag '+status;tag.textContent=status;const agent=document.createElement('strong');agent.textContent=e.agent||'SYSTEM';const msg=document.createElement('div');msg.textContent=e.message||'';const stamp=document.createElement('time');stamp.textContent=time+' ';row.append(stamp,tag,agent,msg);$('#logs').prepend(row);const node=document.querySelector('.node[data-agent="'+(e.agent||'').replaceAll('"','')+'"]');if(node){node.classList.add('active');setTimeout(()=>node.classList.remove('active'),900);}refreshAgents();}
const stream=new EventSource('/api/events');stream.onmessage=(ev)=>logEvent(JSON.parse(ev.data));
async function loadCatalog(){const data=await api('/api/companies');categoryCatalog=data.categories;$('#categories').innerHTML=categoryCatalog.map(c=>'<label class="category"><input type="checkbox" value="'+c.id+'"><span>'+c.label+'</span></label>').join('');$('#categories').addEventListener('change',()=>{selected=[...$('#categories').querySelectorAll('input:checked')].map(x=>x.value);});}
async function refreshInbox(){const data=await api('/api/dev-inbox');$('#inbox-list').innerHTML=data.messages.length?data.messages.map(m=>'<div class="inbox-row"><span>'+m.channel.toUpperCase()+' · '+m.destination.replaceAll('<','&lt;')+'</span><b>'+m.code+'</b></div>').join(''):'No OTP messages yet.';}
$('#channel').addEventListener('change',()=>{const mobile=$('#channel').value==='mobile';$('#destination-label').firstChild.textContent=mobile?'MOBILE NUMBER':'EMAIL ADDRESS';$('#destination').type=mobile?'tel':'email';$('#destination').value=mobile?'+910000000001':'asha@example.com';});
$('#send-otp').addEventListener('click',async()=>{try{if(!selected.length)throw new Error('Select at least one data category.');const data=await api('/api/intake/otp',{method:'POST',body:JSON.stringify({company_id:'novamart',customer_id:$('#customer-id').value.trim(),channel:$('#channel').value,destination:$('#destination').value.trim()})});sessionId=data.session_id;verified=false;$('#otp-code').disabled=false;$('#verify-otp').disabled=false;$('#submit-request').disabled=true;$('#step-label').textContent='STEP 2 / 3';message('OTP generated in the offline Dev Inbox. Expires in 5 minutes.','success');await refreshInbox();}catch(e){message(e.message,'error');}});
$('#verify-otp').addEventListener('click',async()=>{try{await api('/api/intake/verify',{method:'POST',body:JSON.stringify({session_id:sessionId,code:$('#otp-code').value.trim()})});verified=true;$('#submit-request').disabled=false;$('#verify-otp').disabled=true;$('#otp-code').disabled=true;$('#step-label').textContent='STEP 3 / 3';message('OTP verified. You can now submit this request.','success');}catch(e){message(e.message,'error');}});
$('#submit-request').addEventListener('click',async()=>{try{const result=await api('/api/intake/submit',{method:'POST',body:JSON.stringify({session_id:sessionId,categories:selected})});$('#submit-request').disabled=true;$('#request-count').textContent=String(Number($('#request-count').textContent)+1);$('#request-result').textContent='Request '+result.request_id+' received · '+result.selected_categories.length+' categories · '+result.status;$('#request-result').className='request-result';$('#step-label').textContent='DISCOVERY RUNNING';message('Request accepted. Discovery Agent is searching only the selected categories.','success');try{const companyResult=await api('/api/deletion-request/'+encodeURIComponent(result.request_id),{method:'POST'});if(companyResult.company_ticket){$('#request-result').textContent='NovaMart ticket '+companyResult.company_ticket+' · '+companyResult.status+' · '+companyResult.requested_categories.length+' categories sent';message('Company received the deletion request. NovaMart must review and execute any approved deletion. Nothing was deleted by our agents.','success');$('#step-label').textContent='AWAITING COMPANY';const action=document.createElement('div');action.className='company-action';action.innerHTML='<p>MOCK COMPANY CONSOLE · SYNTHETIC DATA ONLY</p><button id="company-approve">SIMULATE NOVAMART STAFF APPROVAL</button><small>Explicit demo operator action. This is not a real company connection.</small>';$('#request-result').append(action);$('#company-approve').addEventListener('click',async()=>{try{$('#company-approve').disabled=true;const done=await api('/api/company/approve/'+encodeURIComponent(companyResult.company_ticket),{method:'POST'});message('NovaMart demo operator action completed. Independent verification starting.','success');$('#step-label').textContent='VERIFYING';const v=await api('/api/verify/'+encodeURIComponent(result.request_id),{method:'POST'});$('#request-result').append(document.createTextNode(' · Verification: '+v.status+' · leftovers: '+v.leftover_count));message(v.message,v.status==='VERIFIED'?'success':'error');$('#step-label').textContent=v.status;}catch(e){$('#company-approve').disabled=false;message(e.message,'error');}});}else{$('#request-result').textContent='Discovery completed · no deletion request submitted';message('Selected categories require review/retention under the illustrative demo rules. No deletion was performed.','success');$('#step-label').textContent='REVIEW REQUIRED';}}catch(workflowError){message('Request accepted, but company request could not be submitted: '+workflowError.message,'error');$('#step-label').textContent='COMPANY REQUEST WAITING';}}catch(e){message(e.message,'error');}});
$('#refresh-inbox').addEventListener('click',refreshInbox);
$('#clear').addEventListener('click',()=>$('#logs').innerHTML='<div class="empty">Event view cleared.</div>');
loadCatalog().catch(e=>message(e.message,'error'));refreshAgents();refreshInbox();

async function refreshAudit(){
  try{
    const [events, integrity] = await Promise.all([api('/api/audit'), api('/api/audit/verify')]);
    $('#audit-status').textContent = integrity.valid
      ? '● CHAIN VALID · '+integrity.checked+' RECORDS'
      : '● INTEGRITY FAILURE · CHECK RECORD '+integrity.checked;
    $('#audit-status').className = 'audit-status '+(integrity.valid?'valid':'invalid');
    $('#audit-list').innerHTML = events.events.length ? events.events.map(e =>
      '<div class="audit-row"><b>#'+e.sequence+' · '+e.agent+'</b><span>'+e.action+' · '+e.outcome+'</span><small>'+e.timestamp+' · '+e.item_count+' item(s) · '+e.categories.join(', ')+'</small></div>'
    ).join('') : 'No audit events yet.';
  }catch(error){$('#audit-status').textContent='Audit service unavailable: '+error.message;}
}
$('#verify-audit').addEventListener('click',refreshAudit);
refreshAudit();

setInterval(refreshAudit, 5000);
