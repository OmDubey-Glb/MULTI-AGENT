const $ = (s) => document.querySelector(s);
async function refreshAgents(){const r=await fetch('/api/agents');const d=await r.json();$('#agent-list').innerHTML=d.agents.map(a=>`<div class="agent"><span>${a.name}</span><b>${a.status}</b></div>`).join('');}
function logEvent(e){const empty=$('.empty');if(empty)empty.remove();const row=document.createElement('div');row.className='log';const time=new Date(e.timestamp||Date.now()).toLocaleTimeString();const status=e.status||'INFO';row.innerHTML=`<time>${time}</time><span class="tag ${status}">${status}</span><strong>${e.agent||'SYSTEM'}</strong><br>${e.message||''}`;$('#logs').prepend(row);const node=document.querySelector(`.node[data-agent="${CSS.escape(e.agent||'')}"]`);if(node){node.classList.add('active');setTimeout(()=>node.classList.remove('active'),900);}}
const stream=new EventSource('/api/events');stream.onmessage=(ev)=>logEvent(JSON.parse(ev.data));
$('#run-demo').addEventListener('click',()=>logEvent({agent:'Orchestrator',status:'INFO',message:'Dashboard connected. Full agent workflow is the next implementation milestone.'}));
$('#clear').addEventListener('click',()=>$('#logs').innerHTML='<div class="empty">Event view cleared.</div>');
refreshAgents();
