/* Scenario presentation only. Input, retries and reconnect use Astral transport. */
(() => {
  const node = id => document.getElementById(id);
  function paragraphs(id, texts) { node(id).replaceChildren(...texts.map(text => {const p=document.createElement('p');p.textContent=text;return p;})); }
  async function desk() {
    try {
      const state = await (await fetch('api/state', {cache:'no-store'})).json();
      const s = state.casebook;
      node('resources').textContent = `${state.map[s.location].name} · $${s.cash} · Injury ${s.injury}/3 · Heat ${s.heat}/5`;
      paragraphs('casebook', [s.neighbourhood, ...Object.values(s.evidence).map(e=>`${e.text} — ${e.source} (${e.credibility}/3)`) ]);
      paragraphs('obligations', [...s.promises, ...s.debts, ...(!s.promises.length&&!s.debts.length?['No promises or debts.']:[])]);
      paragraphs('city', Object.entries(state.map).map(([key,p])=>`${p.name} [${key}] → ${p.exits.join(', ')}`).concat(Object.values(state.contacts).map(p=>`${p[0]} · ${p[1]} · ${p[2]}`)));
      paragraphs('jobs', Object.entries(state.jobs).map(([key,j])=>`${s.jobs[key]?.startsWith('complete:')?'SETTLED':s.jobs[key]?'IN PROGRESS':'AVAILABLE'} · ${key} at ${j.place}: ${j.description}`));
      const signature=state.suggestions.join('|');
      if(node('suggestions').dataset.signature!==signature) {
        node('suggestions').dataset.signature=signature;
        node('suggestions').replaceChildren(...state.suggestions.map(text=>{const b=document.createElement('button');b.type='button';b.textContent=text;b.onclick=()=>{node('command').value=text;node('command').dispatchEvent(new Event('input'));node('command').focus();};return b;}));
      }
      node('pause-status').textContent=state.pause_after?'Will pause after your next action resolves.':'';
    } catch {} finally {setTimeout(desk,2000);}
  }
  async function control(path) {
    try { const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-Astral-Client':'1'},body:'{}'});if(!r.ok)throw Error();node('pause-status').textContent=path.includes('resume')?'Resuming…':'Pause armed; submit your intended action.'; }
    catch {node('pause-status').textContent='Could not reach host. Please retry.';}
  }
  node('pause-next').onclick=()=>control('api/pause-after-action');
  node('resume').onclick=()=>control('api/resume');
  desk();
})();
