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
async function offerBoundedRetry(requestId, container) {
  const retry = document.createElement('button');
  retry.textContent = 'SUBMIT BOUNDED COMPANY RETRY';
  retry.addEventListener('click', async () => {
    try {
      retry.disabled = true;
      const submitted = await api('/api/retry/' + encodeURIComponent(requestId), {method:'POST'});
      const line = document.createElement('p');
      line.textContent = 'Retry ' + submitted.retry_count + '/' + submitted.max_retries + ' · NovaMart ticket ' + submitted.company_ticket + ' · approval required';
      container.append(line);
      const approve = document.createElement('button');
      approve.textContent = 'SIMULATE COMPANY STAFF APPROVAL FOR RETRY';
      approve.addEventListener('click', async () => {
        try {
          approve.disabled = true;
          await api('/api/company/approve/' + encodeURIComponent(submitted.company_ticket), {method:'POST'});
          const checked = await api('/api/verify/' + encodeURIComponent(requestId), {method:'POST'});
          const result = document.createElement('p');
          result.textContent = 'Retry verification: ' + checked.status + ' · leftovers: ' + checked.leftover_count;
          container.append(result);
          message(checked.message, checked.status === 'VERIFIED' ? 'success' : 'error');
          if (checked.status === 'LEFTOVERS_FOUND') offerBoundedRetry(requestId, container);
        } catch (error) {
          approve.disabled = false;
          message(error.message, 'error');
        }
      });
      container.append(approve);
      message(submitted.message, 'success');
    } catch (error) {
      retry.disabled = false;
      message(error.message, 'error');
    }
  });
  container.append(retry);
}
async function refreshAgents(){try{const d=await api('/api/agents');$('#agent-list').innerHTML=d.agents.map(a=>'<div class="agent"><span>'+a.name+'</span><b>'+a.status+'</b></div>').join('');}catch{}}
function logEvent(e){const empty=$('.empty');if(empty)empty.remove();const row=document.createElement('div');row.className='log';const time=new Date(e.timestamp||Date.now()).toLocaleTimeString();const status=e.status||'INFO';const tag=document.createElement('span');tag.className='tag '+status;tag.textContent=status;const agent=document.createElement('strong');agent.textContent=e.agent||'SYSTEM';const msg=document.createElement('div');msg.textContent=e.message||'';const stamp=document.createElement('time');stamp.textContent=time+' ';row.append(stamp,tag,agent,msg);$('#logs').prepend(row);const node=document.querySelector('.node[data-agent="'+(e.agent||'').replaceAll('"','')+'"]');if(node){node.classList.add('active');setTimeout(()=>node.classList.remove('active'),900);}refreshAgents();}
const stream=new EventSource('/api/events');stream.onmessage=(ev)=>logEvent(JSON.parse(ev.data));
async function loadCatalog(){const data=await api('/api/companies');categoryCatalog=data.categories;const removable=categoryCatalog.filter(c=>!['RETAIN','REVIEW'].includes(c.action));const review=categoryCatalog.filter(c=>['RETAIN','REVIEW'].includes(c.action));const render=items=>items.map(c=>'<label class="category"><input type="checkbox" value="'+c.id+'"><span>'+c.label+'</span><em>'+(c.action==='ANONYMIZE'?'ANONYMIZE':'REQUEST')+'</em></label>').join('');$('#categories').innerHTML=render(removable)||'<span class="muted">No directly requestable categories in this demo catalog.</span>';$('#retained-categories').innerHTML=review.map(c=>'<div class="retained-item"><b>'+c.label+'</b><small>'+c.reason+'</small><span>'+c.action+'</span></div>').join('');document.querySelector('.wizard').addEventListener('change',e=>{if(e.target.matches('#categories input[type=checkbox]')){selected=[...$('#categories').querySelectorAll('input:checked')].map(x=>x.value);$('#submit-request').disabled=!selected.length;}});}
async function refreshInbox(){const data=await api('/api/dev-inbox');$('#inbox-list').innerHTML=data.messages.length?data.messages.map(m=>'<div class="inbox-row"><span>'+m.channel.toUpperCase()+' · '+m.destination.replaceAll('<','&lt;')+'</span><b>'+m.code+'</b></div>').join(''):'No OTP messages yet.';}
$('#channel').addEventListener('change',()=>{const mobile=$('#channel').value==='mobile';$('#destination-label').childNodes[0].textContent=mobile?'MOBILE NUMBER':'EMAIL ADDRESS';$('#destination').type=mobile?'tel':'email';$('#destination').value=mobile?'+910000000001':'asha@example.com';$('#destination').placeholder=mobile?'+91 XXXXX XXXXX':'name@example.com';});
$('#send-otp').addEventListener('click',async()=>{try{const data=await api('/api/intake/otp',{method:'POST',body:JSON.stringify({company_id:'novamart',customer_id:$('#customer-id').value.trim(),channel:$('#channel').value,destination:$('#destination').value.trim()})});sessionId=data.session_id;verified=false;$('#otp-code').value='';$('#otp-code').disabled=false;$('#verify-otp').disabled=false;$('#submit-request').disabled=true;$('#step-label').textContent='VERIFY ACCOUNT';await refreshInbox();const inboxData=await api('/api/dev-inbox');const generated=inboxData.messages.find(item=>item.session_id===sessionId);const reveal=$('#otp-demo-code');if(generated&&reveal){reveal.hidden=false;reveal.innerHTML='DEMO OTP <strong>'+generated.code+'</strong><small>Local offline demo only · valid for 5 minutes · no email/SMS is sent</small>';}message('Your demo OTP is ready below. Enter the 6 digits to continue.','success');}catch(e){message(e.message,'error');}});
$('#verify-otp').addEventListener('click',async()=>{try{await api('/api/intake/verify',{method:'POST',body:JSON.stringify({session_id:sessionId,code:$('#otp-code').value.trim()})});verified=true;$('#verify-otp').disabled=true;$('#otp-code').disabled=true;message('Account verified. Loading your NovaMart data categories…','success');await runTransition('Account verified','Intake Agent confirmed the OTP. Preparing your personal data inventory.',1);$('#wizard-step-one').classList.remove('active');$('#wizard-step-two').classList.add('active');$('#step-label').textContent='STEP 2 / 2';$('#progress-two').classList.add('progress-active');}catch(e){message(e.message,'error');}});
$('#submit-request').addEventListener('click',async()=>{try{await runTransition('Intake Agent · Request accepted','Validating your selected categories and preparing the request record.',0.22);const result=await api('/api/intake/submit',{method:'POST',body:JSON.stringify({session_id:sessionId,categories:selected})});$('#submit-request').disabled=true;$('#request-count').textContent=String(Number($('#request-count').textContent)+1);$('#request-result').textContent='Request '+result.request_id+' received · '+result.selected_categories.length+' categories · '+result.status;$('#request-result').className='request-result';$('#step-label').textContent='DISCOVERY RUNNING';message('Request accepted. Specialist agents are processing the selected scope.','success');try{await runTransition('Discovery Agent · Data inventory','Searching only the categories you selected in NovaMart demo systems.',0.48);await runTransition('Deletion Request Agent · Draft preparation','Preparing a company-side erasure request. No data is deleted by CHAUKIDAR.AI.',0.72);const companyResult=await api('/api/deletion-request/'+encodeURIComponent(result.request_id),{method:'POST'});await runTransition('Audit Agent · Evidence recorded','The workflow action is written to the privacy-minimized audit hash chain.',0.86);await runTransition('Monitoring Agent · Request tracked','The request, company ticket status and deadline are registered for monitoring.',0.96);if(companyResult.company_ticket){$('#request-result').textContent='NovaMart ticket '+companyResult.company_ticket+' · '+companyResult.status+' · '+companyResult.requested_categories.length+' categories sent';message('Company received the deletion request. NovaMart must review and execute any approved deletion. Nothing was deleted by our agents.','success');$('#step-label').textContent='AWAITING COMPANY';const action=document.createElement('div');action.className='company-action';action.innerHTML='<p>MOCK COMPANY CONSOLE · SYNTHETIC DATA ONLY</p><button id="company-approve">SIMULATE NOVAMART STAFF APPROVAL</button><small>Explicit demo operator action. This is not a real company connection.</small>';$('#request-result').append(action);$('#company-approve').addEventListener('click',async()=>{try{$('#company-approve').disabled=true;await runTransition('NovaMart company review','The company operator is reviewing and executing the approved synthetic-data request.',0.9);const done=await api('/api/company/approve/'+encodeURIComponent(companyResult.company_ticket),{method:'POST'});message('NovaMart demo operator action completed. Independent verification starting.','success');$('#step-label').textContent='VERIFYING';await runTransition('Verification Agent · Independent check','Re-scanning the same selected categories to confirm the company-reported outcome.',1);const v=await api('/api/verify/'+encodeURIComponent(result.request_id),{method:'POST'});$('#request-result').append(document.createTextNode(' · Verification: '+v.status+' · leftovers: '+v.leftover_count));message(v.message,v.status==='VERIFIED'?'success':'error');$('#step-label').textContent=v.status;if(v.status==='LEFTOVERS_FOUND')offerBoundedRetry(result.request_id,$('#request-result'));}catch(e){$('#company-approve').disabled=false;message(e.message,'error');}});}else{$('#request-result').textContent='Discovery completed · no deletion request submitted';message('Selected categories require review/retention under the illustrative demo rules. No deletion was performed.','success');$('#step-label').textContent='REVIEW REQUIRED';}}catch(workflowError){message('Request accepted, but company request could not be submitted: '+workflowError.message,'error');$('#step-label').textContent='COMPANY REQUEST WAITING';}}catch(e){message(e.message,'error');}});
$('#back-to-verify').addEventListener('click',()=>{$('#wizard-step-two').classList.remove('active');$('#wizard-step-one').classList.add('active');$('#step-label').textContent='STEP 1 / 2';$('#progress-two').classList.remove('progress-active');});
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

async function refreshMonitoring(){
  try{
    const data=await api('/api/monitoring');
    const s=data;
    $('#monitor-summary').textContent='TOTAL '+s.total+'  ·  PENDING COMPANY '+s.pending_company+'  ·  DEADLINE BREACH '+s.overdue+'  ·  RETRY LIMIT '+s.retry_limit_reached+'  ·  MAX RETRIES '+s.max_retries;
    $('#monitor-list').innerHTML=s.requests.length?s.requests.map(r=>{
      const deadline=new Date(r.deadline_at).toLocaleString();
      return '<div class="monitor-row"><b>'+r.request_id+' · '+r.status+'</b><span>Deadline: '+deadline+' · Retry '+r.retry_count+'/'+s.max_retries+'</span><small>'+(r.company_ticket||'No company ticket')+(r.alert?' · '+r.alert:'')+'</small></div>';
    }).join(''):'No requests being monitored yet.';
  }catch(error){$('#monitor-summary').textContent='Monitoring unavailable: '+error.message;}
}
$('#refresh-monitor').addEventListener('click',refreshMonitoring);
setInterval(refreshMonitoring,10000);
refreshMonitoring();

/* Click any agent node or status row to open its interactive profile. */
const agentProfiles={
"Orchestrator":{c:"#39d9ff",d:"Coordinates the complete request workflow and hands work to the six specialist agents.",t:["Routes each request through the correct workflow stages.","Passes the exact selected categories between agents.","Coordinates status updates, hand-offs and bounded retries.","Keeps company approval separate from AI coordination."],r:"Coordinates the process; it does not directly delete company data."},
"Intake":{c:"#23e0a0",d:"Validates incoming erasure requests and performs the offline demo OTP verification step.",t:["Checks customer details and selected categories.","Starts and verifies the demo OTP.","Applies configurable illustrative policy rules.","Preserves the user's exact selected scope."],r:"The offline OTP is a demo mechanism, not real-world identity proof."},
"Discovery":{c:"#a78bfa",d:"Searches NovaMart's synthetic demo systems for records matching the customer and selected categories.",t:["Calls the company-authorized discovery endpoint.","Collects matching record and system references.","Reports the inventory to the orchestrator.","Does not expand the selected request scope."],r:"Discovery is read-only and uses synthetic data only."},
"Deletion Request":{c:"#ffad4d",d:"Prepares and submits a scoped erasure request to the NovaMart mock company API.",t:["Builds a request from discovered item references.","Submits the request to the company API.","Tracks the company ticket and response.","Waits for explicit company staff approval in the demo."],r:"NovaMart—not CHAUKIDAR.AI—remains responsible for approving and executing deletion."},
"Verification":{c:"#55e6c1",d:"Independently checks whether company-approved actions removed the selected records.",t:["Waits for company execution to complete.","Runs a fresh scan of the same selected scope.","Reports verified results or remaining records.","Can request a bounded retry when leftovers remain."],r:"Verification reports evidence; it does not perform deletion."},
"Audit":{c:"#b69aff",d:"Records important workflow events in a privacy-minimized, tamper-evident SHA-256 hash chain.",t:["Records agent actions, outcomes and item counts.","Uses a keyed subject hash instead of raw identifiers.","Links records into a verifiable hash chain.","Exposes an integrity check for audit history."],r:"The local demo chain is not a replacement for production-grade external anchoring."},
"Monitoring":{c:"#ffad4d",d:"Tracks deadlines, company tickets, retry budgets and workflow exceptions.",t:["Tracks request status and configured deadlines.","Enforces the retry limit.","Raises alerts and opens human-review tickets.","Highlights overdue or blocked requests."],r:"The prototype checks monitoring through its API; it has no production background scheduler."}
};
const agentModal=$('#agent-modal'),particleCanvas=$('#agent-particles'),agentOrb=$('#energy-orb');
function showAgent(name){
 const p=agentProfiles[name];if(!p)return;
 $('#agent-modal-title').textContent=name;
 $('#agent-description').textContent=p.d;
 $('#agent-tasks').replaceChildren(...p.t.map(x=>{const li=document.createElement('li');li.textContent=x;return li;}));
 $('#agent-responsibility').textContent=p.r;
 agentModal.style.setProperty('--agent-color',p.c);
 agentModal.classList.add('visible');agentModal.setAttribute('aria-hidden','false');
 startAgentOrb(p.c);
}
function hideAgent(){agentModal.classList.remove('visible');agentModal.setAttribute('aria-hidden','true');if(window.agentOrbFrame)cancelAnimationFrame(window.agentOrbFrame);}
$('#agent-close').addEventListener('click',hideAgent);
agentModal.addEventListener('click',e=>{if(e.target===agentModal)hideAgent();});
document.addEventListener('keydown',e=>{if(e.key==='Escape')hideAgent();});
document.querySelectorAll('.node[data-agent]').forEach(n=>{n.setAttribute('role','button');n.setAttribute('tabindex','0');n.addEventListener('click',()=>showAgent(n.dataset.agent));n.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();showAgent(n.dataset.agent);}});});
const agentListRoot=$('#agent-list');
agentListRoot.addEventListener('click',e=>{const row=e.target.closest('.agent');if(row)showAgent(row.querySelector('span')?.textContent.trim());});
agentListRoot.addEventListener('keydown',e=>{const row=e.target.closest('.agent');if(row&&(e.key==='Enter'||e.key===' ')){e.preventDefault();showAgent(row.querySelector('span')?.textContent.trim());}});
const agentListObserver=new MutationObserver(()=>agentListRoot.querySelectorAll('.agent').forEach(row=>{row.setAttribute('role','button');row.setAttribute('tabindex','0');row.title='Click to learn what this agent does';}));
agentListObserver.observe(agentListRoot,{childList:true});
let orbParticles=[],orbCtx=null;
function startAgentOrb(color){
 if(window.agentOrbFrame)cancelAnimationFrame(window.agentOrbFrame);
 const rect=particleCanvas.getBoundingClientRect(),dpr=Math.min(devicePixelRatio||1,2);
 particleCanvas.width=Math.max(1,rect.width*dpr);particleCanvas.height=Math.max(1,rect.height*dpr);
 orbCtx=particleCanvas.getContext('2d');orbCtx.setTransform(dpr,0,0,dpr,0,0);
 const w=rect.width,h=rect.height,cx=w/2,cy=h/2;
 orbParticles=Array.from({length:75},()=>({x:cx+(Math.random()-.5)*130,y:cy+(Math.random()-.5)*130,vx:(Math.random()-.5)*.8,vy:(Math.random()-.5)*.8,r:Math.random()*2+0.5,a:Math.random()*.7+.2,life:Math.random()*120}));
 function draw(){
  if(!agentModal.classList.contains('visible'))return;
  orbCtx.clearRect(0,0,w,h);
  orbParticles.forEach(p=>{p.x+=p.vx;p.y+=p.vy;p.life++;if(Math.hypot(p.x-cx,p.y-cy)>100||p.life>180){p.x=cx+(Math.random()-.5)*38;p.y=cy+(Math.random()-.5)*38;p.life=0;}orbCtx.globalAlpha=p.a*(.7+.3*Math.sin(p.life*.08));orbCtx.fillStyle=color;orbCtx.beginPath();orbCtx.arc(p.x,p.y,p.r,0,Math.PI*2);orbCtx.fill();});
  orbCtx.globalAlpha=1;window.agentOrbFrame=requestAnimationFrame(draw);
 }
 draw();
}
$('#agent-visual').addEventListener('pointerdown',e=>{
 const r=particleCanvas.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;
 for(let i=0;i<32;i++){const a=Math.random()*Math.PI*2,s=1+Math.random()*3;orbParticles.push({x,y,vx:Math.cos(a)*s,vy:Math.sin(a)*s,r:1+Math.random()*2,a:1,life:0});}
 orbParticles=orbParticles.slice(-120);agentOrb.classList.remove('burst');void agentOrb.offsetWidth;agentOrb.classList.add('burst');
});

/* Dedicated clickable specialist-agent navigation in the sidebar */
document.querySelectorAll('.agent-nav[data-profile]').forEach(button=>{
 button.addEventListener('click',()=>showAgent(button.dataset.profile));
});

/* Full-screen, staged transition used between guided request steps. */
const processingSteps=[
 ["Intake Agent","Validating the verified request and preserving the selected data scope."],
 ["Discovery Agent","Searching NovaMart's synthetic account systems for matching records."],
 ["Deletion Request Agent","Preparing a scoped erasure draft for NovaMart's authorized team."],
 ["Audit Agent","Recording a privacy-minimized event in the audit trail."],
 ["Monitoring Agent","Registering deadlines, ticket status and retry limits."]
];
async function runTransition(title,description,progress=0){
 const layer=$('#agent-processing');$('#processing-title').textContent=title;$('#processing-description').textContent=description;$('#processing-fill').style.width=(progress*100)+'%';layer.classList.add('visible');layer.setAttribute('aria-hidden','false');await new Promise(resolve=>setTimeout(resolve,1500));layer.classList.remove('visible');layer.setAttribute('aria-hidden','true');
}
