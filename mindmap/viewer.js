import { Markmap } from 'markmap-view';
const selector = document.querySelector('#map-select');
fetch('./map.json', { cache: 'no-store' }).then(r => { if (!r.ok) throw Error(r.status); return r.json(); }).then(initialMaps => {
  let maps = initialMaps;
  let map;
  let displayedId;
  const nodeKey = node => node.payload?.liveId || node.content;
  let showAllTasks = false;
  const show = async () => {
    const id = location.hash.slice(1) || 'server5-commandcenter';
    let frame=document.querySelector('#organic-current');
    const organic=id==='current-projects';
    if(organic && !frame){frame=document.createElement('iframe');frame.id='organic-current';frame.src='./current-projects.html';frame.title='Current Projects';frame.style.cssText='width:100%;flex:1;border:0';document.body.append(frame);}
    if(frame) frame.hidden=!organic;
    document.querySelector('#mindmap').style.display=organic?'none':'';
    document.querySelector('#current-tasks').hidden=true;
    document.querySelector('header + small').hidden=organic;
    if(organic){selector.value=id;document.querySelector('#status').textContent='';return;}

    if (!Object.hasOwn(maps, id)) {
      document.querySelector('#status').textContent = 'Onbekende kaart; kies een kaart.';
      return;
    }
    selector.value = id;
    document.title = `${selector.selectedOptions[0].textContent} – Markmap`;
    const sameMap = map && displayedId === id;
    const folds = new Map();
    const remember = node => {
      folds.set(nodeKey(node), node.payload?.fold || 0);
      (node.children || []).forEach(remember);
    };
    if (sameMap) remember(map.state.data);
    const data = structuredClone(maps[id]);
    let latestTask = '';
    const taskSection = document.querySelector('#current-tasks');
    taskSection.replaceChildren();
    taskSection.hidden = id !== 'current-projects';
    const labels = {queued:'queued', running:'running', review:'succeeded · beoordeling open', accepted:'accepted', failed:'failed / blocked'};
    // Receipt timestamps describe the latest lifecycle event for each task.
    const allTasks = [...(maps.taskStatus || [])].sort((a,b) =>
      (Date.parse(b.at) || 0) - (Date.parse(a.at) || 0));
    const active = task => ['running', 'queued'].includes(task.status);
    const lastCompleted = allTasks.find(task => !active(task));
    const renderTasks = () => {
      taskSection.replaceChildren();
      const toggle = document.createElement('button');
      toggle.textContent = showAllTasks ? 'Alle taken verbergen' : 'Alle taken tonen';
      toggle.setAttribute('aria-expanded', String(showAllTasks));
      toggle.onclick = () => { showAllTasks = !showAllTasks; show(); };
      taskSection.append(toggle);
      const tasks = showAllTasks ? allTasks : [
        ...allTasks.filter(active), ...(lastCompleted ? [lastCompleted] : [])
      ];
      for (const task of tasks) {
        const color = task.status === 'accepted' || (task.status === 'succeeded' && task.accepted)
          ? 'accepted' : ({succeeded:'review',review:'review',running:'running',queued:'queued'}[task.status] || 'failed');
        const row = document.createElement('div');
        row.className = `task-${color}`;
        row.textContent = `${task.id} — ${task.status}${task.status === 'succeeded' ? (task.accepted ? ' · accepted' : ' · beoordeling open') : ''}`;
        taskSection.append(row);
      }
      if (!tasks.length) {
        const empty = document.createElement('div');
        empty.textContent = 'Geen brokergegevens beschikbaar';
        taskSection.append(empty);
      }
    };
    renderTasks();
    // Transient viewer projection; source and published tree remain untouched.
    if (id === 'current-projects') {
      const prune = node => {
        node.children = (node.children || []).filter(child => !/^\[TASK:/u.test(child.content));
        node.children.forEach(prune);
      };
      prune(data);
      const findProject = node => node.content.includes('[PROJECT:SERVER5]')
        ? node : (node.children || []).map(findProject).find(Boolean);
      const project = findProject(data);
      const escape = value => String(value).replace(/[&<>"']/gu, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
      const visibleTasks = showAllTasks ? allTasks : [...allTasks.filter(active), ...(lastCompleted ? [lastCompleted] : [])];
      // fold=2 exempts the subtree from Markmap's initial depth cutoff.
      const openPath = node => {
        if (node === project || (node.children || []).some(openPath)) {
          node.payload = {...node.payload, fold: 2};
          return true;
        }
        return false;
      };
      if (!sameMap) openPath(data);
      if (project) project.children.unshift({
        content: '🔄 Codex — actuele opdrachten',
        payload: {liveId: 'codex-current-tasks', fold: 2},
        children: visibleTasks.map(task => {
          const color = task.status === 'accepted' || (task.status === 'succeeded' && task.accepted)
            ? 'accepted' : ({succeeded:'review',review:'review',running:'running',queued:'queued'}[task.status] || 'failed');
          const label = task.status + (task.status === 'succeeded' ? (task.accepted ? ' · accepted' : ' · beoordeling open') : '');
          return {content: `${escape(task.id)} — ${escape(label)}`, children: [],
            payload: {liveId: `codex-task:${task.id}`, taskId: task.id, taskColor: color}};
        })
      });
    }
    const highlightCurrent = node => {
      const text = document.createElement('span');
      text.innerHTML = node.content;
      const color = node.payload?.taskColor;
      if (Object.hasOwn(labels, color)) {
        latestTask = `${node.payload?.taskId || text.textContent.match(/^\[TASK:([^\]]+)\]/u)?.[1] || 'onbekende taak'} — ${labels[color]}`;
        node.content = `<strong class="task-${color}">${node.content}</strong>`;
      }
      else if (!/^\[TASK:/u.test(text.textContent) && !text.textContent.includes('[LINK-TASK:') && text.textContent.includes('🔄 HUIDIGE STAP —')) node.content = `<strong class="current-step">${node.content}</strong>`;
      (node.children || []).forEach(highlightCurrent);
    };
    if (id === 'current-projects') highlightCurrent(data);
    if (sameMap) {
      const restore = node => {
        if (folds.has(nodeKey(node))) node.payload = {...node.payload, fold: folds.get(nodeKey(node))};
        (node.children || []).forEach(restore);
      };
      restore(data);
      // Preserve user folds and SVG zoom transform on automatic updates.
      await map.setData(data, {initialExpandLevel: -1});
    } else {
      if (map) map.destroy();
      map = Markmap.create('#mindmap', { duration: 200, maxWidth: 400, initialExpandLevel: id === 'current-projects' ? 3 : 2 });
      displayedId = id;
      // Complete layout before the one initial fit.
      await map.setData(data);
      await map.fit();
    }
    document.querySelector('#status').textContent = (latestTask ? `Nieuwste taak: ${latestTask}. ` : '') + 'Sleep · scroll om te zoomen · klik op de rondjes om takken te openen/sluiten';
  };
  selector.onchange = () => { location.hash = selector.value; };
  window.addEventListener('hashchange', show);
  document.querySelector('#fit').onclick = () => map?.fit();
  document.querySelector('#expand').onclick = async () => { if (map) { await map.toggleNode(map.state.data, true); await map.fit(); } };
  show();
  let fetching = false;
  setInterval(async () => {
    if (fetching) return;
    fetching = true;
    try {
      const response = await fetch('./map.json', { cache: 'no-store' });
      if (!response.ok) throw Error(response.status);
      const next = await response.json();
      if (JSON.stringify(next) !== JSON.stringify(maps)) {
        maps = next;
        await show();
      }
    } catch {
      document.querySelector('#status').textContent = 'Automatische update mislukt; laatste kaart blijft zichtbaar.';
    } finally { fetching = false; }
  }, 1000);
}).catch(() => { document.querySelector('#status').textContent = 'Mindmap kon niet worden geladen.'; });
