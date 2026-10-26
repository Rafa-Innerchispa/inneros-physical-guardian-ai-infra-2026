'use strict';
const steps = [
  ['OBSERVE', 'Read synthetic device signals'],
  ['REASON', 'Explain anomaly and policy'],
  ['APPROVE', 'Require human authorization'],
  ['ACT', 'Perform bounded virtual action'],
  ['VERIFY', 'Independent virtual state readback'],
  ['PROVE', 'Tamper-evident audit evidence'],
];
let current = null;
let busy = false;
const $ = (id) => document.getElementById(id);
const setText = (id, text) => { $(id).textContent = String(text); };
const states = {observed:0, analyzed:1, approved:2, executed:3, verified:5, failed_safe:4};

async function call(path, body) {
  const options = body === undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)};
  const response = await fetch(path,options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}
function say(msg, good=false) {setText('toast',msg); $('toast').className = `toast ${good ? 'good' : ''}`;}
function disableActions() {
  const s = current?.status || '';
  $('analyze').disabled = busy || s !== 'observed';
  $('approve').disabled = busy || s !== 'analyzed' || !current?.policy?.allowed;
  $('execute').disabled = busy || s !== 'approved';
  $('verify').disabled = busy || s !== 'executed';
  $('create').disabled = busy;
  $('download').disabled = !current || busy;
}
function stageList() {
  const holder = $('stage-list');
  holder.replaceChildren();
  if (!current) {const d=document.createElement('div');d.className='empty-workflow';d.textContent='Create an incident to begin the six-stage operational loop.';holder.append(d);return;}
  const index = states[current.status] ?? 0;
  for(let i=0;i<steps.length;i++) {
    const [title, subtitle] = steps[i];
    const done = i <= index;
    const active = !done && i === index + 1;
    const row = document.createElement('div'); row.className=`stage ${done?'done':(active?'active':'')}`;
    const circle = document.createElement('div');circle.className='stage-circle';circle.textContent=done?'✓':String(i+1);
    const content=document.createElement('div');
    const h=document.createElement('div');h.className='stage-title';h.textContent=title;
    const p=document.createElement('p');p.className='stage-note';p.textContent=done?(i===5?'Audit integrity ready':`${subtitle} · completed`):subtitle;
    content.append(h,p);row.append(circle,content);holder.append(row);
  }
}
function renderCurrent() {
  stageList();
  $('incident-details').hidden = !current;
  if (current) {
    setText('incident-badge', current.status.toUpperCase());
    setText('incident-id', current.id.slice(0,8));
    setText('incident-title', current.title);
    setText('incident-narrative', current.narration?.narrative || 'Reasoning pending. Select Analyze incident.');
    setText('provider-label', current.narration ? `${current.narration.provider} · ${current.narration.truth}` : 'NOT ANALYZED');
    const signals=$('incident-signals'); signals.replaceChildren();
    for(const s of current.signals) {
      const el=document.createElement('span');el.className='signal';el.textContent=`${s.metric}: ${String(s.value)}`;signals.append(el);
    }
    if(current.narration?.fallback_reason) say(`Provider fallback: ${current.narration.fallback_reason}. Deterministic analysis was used.`);
  } else {
    setText('incident-badge','NO INCIDENT');
  }
  disableActions();
}
async function refresh() {
  const state = await call('/api/state');
  setText('stat-total',state.incidents.length);
  setText('stat-verified',state.incidents.filter(x=>x.status==='verified').length);
  setText('stat-integrity',state.audit_integrity.valid?'VALID':'FAILED');
  $('stat-integrity').className=`stat-number stat-small ${state.audit_integrity.valid?'accent-green':''}`;
  const logs=$('incident-log');logs.replaceChildren();
  if (!state.incidents.length) {const el=document.createElement('div');el.className='log-empty';el.textContent='No evidence recorded yet. Create a synthetic incident above.';logs.append(el);return;}
  for(const incident of state.incidents) {
    const row=document.createElement('div');row.className='audit-row';
    const info=document.createElement('div');info.className='audit-title';info.textContent=incident.title;
    const id=document.createElement('small');id.textContent=`#${incident.id.slice(0,8)} · ${incident.site}`;info.append(id);
    const status=document.createElement('div');const label=document.createElement('span');label.className='state-tag';label.textContent=incident.status.toUpperCase();status.append(label);
    const source=document.createElement('span');source.className='truth-tag';source.textContent=incident.truth;
    row.append(info,status,source);logs.append(row);
  }
}
async function operation(callback) {
  if(busy)return;
  busy=true;disableActions();say('Processing…');
  try {current=await callback();say(`Incident ${current.status.toUpperCase()} · saved in local audit log.`,true);}
  catch(e) {say(e.message);}
  finally {busy=false;renderCurrent();await refresh().catch(e=>say(e.message));}
}
$('create').addEventListener('click',()=>operation(()=>call('/api/incidents',{scenario:$('scenario').value})));
$('analyze').addEventListener('click',()=>operation(()=>call(`/api/incidents/${current.id}/analyze`,{mode:$('mode').value})));
$('approve').addEventListener('click',()=>operation(()=>call(`/api/incidents/${current.id}/approve`,{operator:$('operator').value,action:current.recommended_action})));
$('execute').addEventListener('click',()=>operation(()=>call(`/api/incidents/${current.id}/execute`,{})));
$('verify').addEventListener('click',()=>operation(()=>call(`/api/incidents/${current.id}/verify`,{})));
$('download').addEventListener('click',async()=> {
  if(!current) return;
  try {
    const data=await call(`/api/incidents/${current.id}/evidence`);
    const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;
    a.download=`inneros-evidence-${current.id.slice(0,8)}.json`;a.click();
    URL.revokeObjectURL(url);say('Evidence exported as JSON, labeled as simulated.',true);
  } catch(e) {say(e.message);}
});
refresh().catch(e=>say(`Server unavailable: ${e.message}`));
renderCurrent();
