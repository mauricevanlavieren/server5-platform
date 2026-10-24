const el = id => document.getElementById(id);
const gib = n => Number.isFinite(n) ? `${(n / 1024 ** 3).toFixed(1)} GiB` : 'Onbekend';
function rows(id, items) {
  el(id).replaceChildren(...items.map(([title, status]) => {
    const row = document.createElement('div'); row.className = 'row';
    const name = document.createElement('span'); name.textContent = title;
    const badge = document.createElement('span'); badge.className = 'badge'; badge.textContent = status;
    row.append(name, badge); return row;
  }));
}
function networkRows(hosts) {
  rows('network', hosts.map(host => [
    `${host.hostname || 'Hostnaam onbekend'} · ${host.ip || 'IP onbekend'}`,
    `Bereikbaarheid: Onbekend · Laatste meting: ${host.measured_at ? new Date(host.measured_at).toISOString() : 'Onbekend (exact tijdstip/tijdzone niet vastgelegd)'} · ${host.historical || 'Geen bestaande meting'}`
  ]));
}
async function refresh() {
  try {
    const r = await fetch('dashboard-status.json', {cache:'no-store', signal:AbortSignal.timeout(8000)});
    if (!r.ok) throw Error(`HTTP ${r.status}`);
    const s = await r.json();
    if(s.hostname !== 'server5') throw Error('Onverwachte host');
    el('load').textContent = s.load.map(n=>n.toFixed(2)).join(' / ');
    el('cpu').textContent = `${s.cpu_count ?? '?'} logische CPU’s · load 1 / 5 / 15 min`;
    for (const [id, available, total] of [['ram',s.memory_available_bytes,s.memory_total_bytes],['disk',s.root_free_bytes,s.root_total_bytes]]) {
      el(id).textContent = `${gib(available)} vrij`;
      el(`${id}-detail`).textContent = `${gib(total)} totaal`;
      if (Number.isFinite(total) && total>0 && Number.isFinite(available)) el(`${id}-bar`).value=100*(1-available/total);
      else el(`${id}-bar`).removeAttribute('value');
    }
    const up = s.uptime_seconds;
    el('uptime').textContent = Number.isFinite(up) ? `${Math.floor(up/86400)}d ${Math.floor(up%86400/3600)}u ${Math.floor(up%3600/60)}m` : 'Onbekend';
    networkRows(s.network_center || []);
    rows('services', Object.entries(s.services));
    el('counts').textContent = s.queue.available ? ['queued','running','succeeded','failed','cancelled','interrupted'].map(k=>`${k}: ${s.queue.counts[k]||0}`).join(' · ') : 'Queue niet beschikbaar';
    rows('tasks', s.queue.available ? s.queue.recent.map(t=>[t.id,t.status]) : [['Brokermetadata','Onbekend']]);
    rows('projects', s.projects.available ? (s.projects.items.length ? s.projects.items.map(p=>[p.id,`${p.status} · ${p.stages}/${p.max_stages}`]) : [['Geen brokerprojecten','—']]) : [['Projectmetadata','Niet beschikbaar']]);
    el('time').textContent = `Laatste meting: ${new Date(s.observed_at).toLocaleString('nl-NL')}`;
    el('notice').className = s.stale ? 'bad' : '';
    el('notice').textContent = s.stale ? 'Hostmeting gedeeltelijk onbeschikbaar.' : 'Server5 · live lokale gegevens';
  } catch(e) {
    el('notice').className='bad'; el('notice').textContent=`Verversen mislukt: ${e.message}. Eerdere waarden kunnen verouderd zijn.`;
  }
}
refresh();setInterval(refresh,10000);
