// Only an explicitly available broker queue with a running task is green.
export function codexActive(data) {
  const q = data?.queue;
  return q?.available === true && Number.isInteger(q.counts?.running) && q.counts.running > 0;
}

export function startCodexStatus() {
  const dot = document.createElement('span');
  dot.id = 'codex-live-status';
  dot.setAttribute('role', 'img');
  dot.tabIndex = 0;
  dot.style.cssText = 'position:fixed;top:12px;right:12px;width:14px;height:14px;border-radius:50%;border:2px solid #fff;box-shadow:0 0 0 1px #555;z-index:1000';
  function paint(active) {
    dot.style.backgroundColor = active ? '#16803c' : '#c62828';
    dot.title = active ? 'Codex actief' : 'Codex inactief';
    dot.setAttribute('aria-label', dot.title);
  }
  paint(false);
  document.body.append(dot);
  async function refresh() {
    try {
      const response = await fetch('./dashboard-status.json', {
        cache: 'no-store', signal: AbortSignal.timeout(4000)
      });
      if (!response.ok) throw Error('Queue unavailable');
      paint(codexActive(await response.json()));
    } catch { paint(false); }
    setTimeout(refresh, 3000);
  }
  refresh();
}
